// Bridge control-plane message envelope: encode/decode + the fixed message-type
// enum from docs/bridge/MESSAGE_SCHEMA.md. This header fixes *what* a message is
// allowed to be; wire framing (length-prefix) lives in PosixSocketServer, and
// scene/render semantics live in RenderSession.
#pragma once

#include <json/json.h>

#include <cstdint>
#include <string>

namespace moonray_bridge {

// docs/bridge/MESSAGE_SCHEMA.md "Versioning rule": a single monotonically increasing
// integer identifying the envelope shape and message-type semantics, bumped only on
// a breaking change. Bumped 1 -> 2 in Phase 06: CREATE_SCENE's payload changed from
// an `rdla_path` file reference to a structured `scene_variables` object, and
// UPDATE_OBJECT/UPDATE_CAMERA went from "recognized but unimplemented" to real
// message types with their own required payload shape (see SceneBuilder.h,
// docs/decisions/ADR-0005-structured-scene-protocol.md). No negotiation range yet.
constexpr int kProtocolVersion = 2;

// Defensive cap on a single control-plane message body, enforced before any
// allocation/parse is attempted (ERROR_MODEL.md category 1: untrusted input).
constexpr std::uint32_t kMaxMessageBytes = 16u * 1024u * 1024u;

// The fixed 11-entry message-type enum from MESSAGE_SCHEMA.md "Message set".
enum class MessageType {
    HELLO,
    CAPABILITIES,
    CREATE_SCENE,
    UPDATE_OBJECT,
    UPDATE_CAMERA,
    UPDATE_MATERIAL,
    START_RENDER,
    STOP_RENDER,
    FRAME_UPDATE,
    RENDER_COMPLETE,
    ERROR,
    UNKNOWN // sentinel only: a wire string outside the 11 known types decoded to this
};

const char* messageTypeToString(MessageType type);
MessageType messageTypeFromString(const std::string& s);

// ERROR_MODEL.md categories:
//   1 = scene payload validation, 2 = unsupported feature, 3 = native MoonRay error,
//   4 = bridge process crash (detected by the add-on, not sent over the wire),
//   5 = version/handshake mismatch.
struct ErrorInfo {
    int category = 1;
    std::string code;
    std::string message;
};

struct Envelope {
    int protocolVersion = kProtocolVersion;
    MessageType type = MessageType::UNKNOWN;
    std::string id;
    Json::Value payload{Json::objectValue};
};

// Parses one already length-delimited JSON body (see PosixSocketServer framing)
// into an Envelope. Returns false and fills `error` (category 1) on any shape
// violation: invalid JSON, missing/wrong-typed envelope field, or a `type` string
// outside the fixed enum (MESSAGE_SCHEMA.md: "unknown type -> hard ERROR").
// Never partially mutates native state as a side effect of a failed parse.
bool decodeEnvelope(const std::string& jsonBody, Envelope* out, ErrorInfo* error);

std::string encodeEnvelope(const Envelope& env);

// Convenience: builds and encodes an ERROR envelope correlated to `id`
// (empty string when the failing message's own id could not be recovered).
std::string encodeError(const std::string& id, const ErrorInfo& error);

} // namespace moonray_bridge
