// moonray_bridge: native bridge process.
// docs/phases/04-direct-bridge-prototype.md / docs/phases/06-geometry-camera-lights.md
// / docs/bridge/PROTOCOL.md.
//
// Single-threaded: accepts one client connection at a time, requires a
// successful HELLO handshake before any other message, then dispatches
// CREATE_SCENE / UPDATE_OBJECT / UPDATE_CAMERA / START_RENDER against one
// RenderSession per connection (Phase 06: structured scene schema, see
// SceneBuilder.h/ADR-0005 -- replaces Phase 04/05's raw .rdla-path
// CREATE_SCENE). STOP_RENDER / UPDATE_MATERIAL / FRAME_UPDATE are recognized
// (fixed enum, MESSAGE_SCHEMA.md) but explicitly unimplemented so far (ERROR
// category 2), never silently ignored.
#include "PosixSocketServer.h"
#include "Protocol.h"
#include "RenderSession.h"

#include <moonray/rendering/rndr/RenderContext.h>
#include <moonray/rendering/rndr/RenderOptions.h>

#include <csignal>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>
#include <string>

namespace {

volatile std::sig_atomic_t gShutdownRequested = 0;

void handleShutdownSignal(int)
{
    gShutdownRequested = 1;
}

std::ofstream* gLogFile = nullptr;

std::string timestamp()
{
    char buf[32];
    const std::time_t t = std::time(nullptr);
    std::tm tmv{};
    localtime_r(&t, &tmv);
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &tmv);
    return buf;
}

// Logs to stderr AND, when --log-dir was given, to a file -- ARCHITECTURE.md
// security/trust boundaries: "Blender's console is not an acceptable sole
// error-reporting channel for the bridge."
void logLine(const std::string& msg)
{
    const std::string line = "[" + timestamp() + "] " + msg;
    std::cerr << line << "\n";
    if (gLogFile) {
        (*gLogFile) << line << "\n";
        gLogFile->flush();
    }
}

struct Args {
    std::string socketPath;
    std::string logDir;
};

bool parseArgs(int argc, char** argv, Args* out)
{
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--socket" && i + 1 < argc) {
            out->socketPath = argv[++i];
        } else if (arg == "--log-dir" && i + 1 < argc) {
            out->logDir = argv[++i];
        } else {
            std::cerr << "unrecognized argument: " << arg << "\n";
            return false;
        }
    }
    return !out->socketPath.empty();
}

// Maps a caught exception (RenderSession's own typed errors, or an opaque
// std::exception surfaced from RDL2/MoonRay) to an ERROR_MODEL.md category.
moonray_bridge::ErrorInfo classifyException(const std::exception& e)
{
    using namespace moonray_bridge;
    if (dynamic_cast<const SessionValidationError*>(&e)) {
        return ErrorInfo{1, "SESSION_VALIDATION_ERROR", e.what()};
    }
    if (dynamic_cast<const UnsupportedFeatureError*>(&e)) {
        return ErrorInfo{2, "UNSUPPORTED_FEATURE", e.what()};
    }
    // Anything else (scene_rdl2::except::*, std::exception from MoonRay/RDL2
    // itself) happened after this bridge's own validation already accepted the
    // payload -- ERROR_MODEL.md category 3, "native MoonRay render error".
    return ErrorInfo{3, "NATIVE_RENDER_ERROR", e.what()};
}

void handleConnection(moonray_bridge::Connection& conn, moonray::rndr::RenderOptions& options)
{
    using namespace moonray_bridge;

    bool helloOk = false;
    RenderSession session(options);

    while (true) {
        std::optional<std::string> frame;
        try {
            frame = conn.readFrame();
        } catch (const std::exception& e) {
            logLine(std::string("connection read error, closing: ") + e.what());
            return;
        }
        if (!frame) {
            logLine("client disconnected cleanly");
            return;
        }

        Envelope env;
        ErrorInfo parseError;
        if (!decodeEnvelope(*frame, &env, &parseError)) {
            // Malformed-but-well-framed input: report and keep the connection
            // open (docs/phases/04-direct-bridge-prototype.md: "Malformed input
            // fails cleanly").
            logLine("rejecting malformed message: " + parseError.code + ": " + parseError.message);
            try {
                conn.writeFrame(encodeError("", parseError));
            } catch (const std::exception& e) {
                logLine(std::string("failed to write ERROR reply, closing: ") + e.what());
                return;
            }
            continue;
        }

        if (!helloOk) {
            if (env.type != MessageType::HELLO) {
                ErrorInfo err{1, "HANDSHAKE_REQUIRED", "HELLO must be the first message on a connection"};
                conn.writeFrame(encodeError(env.id, err));
                continue;
            }
            if (env.protocolVersion != kProtocolVersion) {
                ErrorInfo err{5, "VERSION_MISMATCH",
                              "bridge speaks protocol_version " + std::to_string(kProtocolVersion) +
                                  ", client sent " + std::to_string(env.protocolVersion)};
                conn.writeFrame(encodeError(env.id, err));
                logLine("closing connection after HELLO version mismatch");
                return; // MESSAGE_SCHEMA.md: version mismatch ends the connection.
            }
            Envelope reply;
            reply.type = MessageType::HELLO;
            reply.id = env.id;
            reply.payload["bridge_info"] = "moonray_bridge/phase04";
            conn.writeFrame(encodeEnvelope(reply));
            helloOk = true;
            logLine("HELLO ok, client_info=" + env.payload.get("client_info", "").asString());
            continue;
        }

        try {
            switch (env.type) {
            case MessageType::HELLO: {
                ErrorInfo err{1, "ALREADY_SHOOK_HANDS", "HELLO already completed on this connection"};
                conn.writeFrame(encodeError(env.id, err));
                break;
            }
            case MessageType::CAPABILITIES: {
                Envelope reply;
                reply.type = MessageType::CAPABILITIES;
                reply.id = env.id;
                Json::Value features(Json::arrayValue);
                features.append("render.batch");
                features.append("framebuffer.shm.rgba_f32");
                reply.payload["features"] = features;
                conn.writeFrame(encodeEnvelope(reply));
                break;
            }
            case MessageType::CREATE_SCENE: {
                const Json::Value sceneVariables = env.payload.get("scene_variables", Json::Value(Json::objectValue));
                const Json::Value ack = session.createScene(sceneVariables);
                Envelope reply;
                reply.type = MessageType::CREATE_SCENE;
                reply.id = env.id;
                reply.payload = ack;
                conn.writeFrame(encodeEnvelope(reply));
                logLine("CREATE_SCENE ok");
                break;
            }
            case MessageType::UPDATE_OBJECT: {
                const Json::Value ack = session.updateObject(env.payload);
                Envelope reply;
                reply.type = MessageType::UPDATE_OBJECT;
                reply.id = env.id;
                reply.payload = ack;
                conn.writeFrame(encodeEnvelope(reply));
                logLine("UPDATE_OBJECT ok: " + env.payload.get("name", "").asString());
                break;
            }
            case MessageType::UPDATE_CAMERA: {
                const Json::Value ack = session.updateCamera(env.payload);
                Envelope reply;
                reply.type = MessageType::UPDATE_CAMERA;
                reply.id = env.id;
                reply.payload = ack;
                conn.writeFrame(encodeEnvelope(reply));
                logLine("UPDATE_CAMERA ok: " + env.payload.get("name", "").asString());
                break;
            }
            case MessageType::START_RENDER: {
                const std::string mode = env.payload.get("render_mode", "final").asString();
                const Json::Value stats = session.startRender(mode);
                Envelope reply;
                reply.type = MessageType::RENDER_COMPLETE;
                reply.id = env.id;
                reply.payload = stats;
                conn.writeFrame(encodeEnvelope(reply));
                logLine("START_RENDER complete: " + Json::writeString(Json::StreamWriterBuilder{}, stats));
                break;
            }
            case MessageType::STOP_RENDER:
            case MessageType::UPDATE_MATERIAL: {
                ErrorInfo err{2, "NOT_IMPLEMENTED_PHASE06",
                              std::string(messageTypeToString(env.type)) + " is not implemented yet (UPDATE_MATERIAL is Phase 07 scope; STOP_RENDER is Phase 08 scope)"};
                conn.writeFrame(encodeError(env.id, err));
                break;
            }
            case MessageType::FRAME_UPDATE:
            case MessageType::RENDER_COMPLETE:
            case MessageType::ERROR: {
                ErrorInfo err{1, "UNEXPECTED_DIRECTION", "this message type is bridge-to-client only"};
                conn.writeFrame(encodeError(env.id, err));
                break;
            }
            case MessageType::UNKNOWN:
                // decodeEnvelope already rejects an unrecognized string before
                // this point; unreachable in practice.
                break;
            }
        } catch (const std::exception& e) {
            const ErrorInfo err = classifyException(e);
            logLine(std::string("request failed: ") + err.code + ": " + err.message);
            try {
                conn.writeFrame(encodeError(env.id, err));
            } catch (const std::exception& writeErr) {
                logLine(std::string("failed to write ERROR reply, closing: ") + writeErr.what());
                return;
            }
        }
    }
}

} // namespace

int main(int argc, char** argv)
{
    Args args;
    if (!parseArgs(argc, argv, &args)) {
        std::cerr << "usage: moonray_bridge --socket <path> [--log-dir <path>]\n";
        return 2;
    }

    std::ofstream logFile;
    if (!args.logDir.empty()) {
        logFile.open(args.logDir + "/moonray_bridge.log", std::ios::app);
        if (logFile.is_open()) gLogFile = &logFile;
    }

    std::signal(SIGPIPE, SIG_IGN); // a dead client must not kill the bridge on write()
    std::signal(SIGINT, handleShutdownSignal);
    std::signal(SIGTERM, handleShutdownSignal);

    logLine("moonray_bridge starting, socket=" + args.socketPath);

    // One RenderOptions for the whole process lifetime, passed to both
    // initGlobalDriver() and every RenderSession/RenderContext -- mirrors
    // moonray/cmd/raas_cmd/moonray/moonray.cc, which uses a single mOptions
    // for both. initGlobalDriver() must run on the same thread that will call
    // RenderContext::startFrame (that source file's own comment on this call).
    moonray::rndr::RenderOptions options;
    moonray::rndr::initGlobalDriver(options);

    int exitCode = 0;
    try {
        moonray_bridge::PosixSocketServer server(args.socketPath);
        logLine("listening");
        while (!gShutdownRequested) {
            moonray_bridge::Connection conn = server.accept();
            logLine("client connected");
            handleConnection(conn, options);
        }
    } catch (const std::exception& e) {
        logLine(std::string("fatal: ") + e.what());
        exitCode = 1;
    }

    moonray::rndr::cleanUpGlobalDriver();
    logLine("moonray_bridge exiting, code=" + std::to_string(exitCode));
    return exitCode;
}
