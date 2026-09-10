#include "RenderSession.h"
#include "SharedMemoryBuffer.h"

#include <moonray/rendering/rndr/RenderContext.h>
#include <moonray/rendering/rndr/RenderOptions.h>
#include <moonray/rendering/rndr/Types.h>
#include <scene_rdl2/common/fb_util/FbTypes.h>
#include <scene_rdl2/common/math/Vec4.h>

#include <sys/stat.h>
#include <unistd.h>

#include <chrono>
#include <sstream>
#include <thread>

namespace moonray_bridge {

RenderSession::RenderSession(moonray::rndr::RenderOptions& options) : mOptions(options) {}

RenderSession::~RenderSession()
{
    mRenderContext.reset();
    unlinkSharedMemory(mLastShmName);
}

Json::Value RenderSession::createScene(const std::string& rdlaPath)
{
    if (rdlaPath.empty()) {
        throw SessionValidationError("CREATE_SCENE payload field 'rdla_path' must be a non-empty string");
    }
    struct stat st{};
    if (stat(rdlaPath.c_str(), &st) != 0) {
        throw SessionValidationError("rdla_path does not exist or is not accessible: " + rdlaPath);
    }
    if (!S_ISREG(st.st_mode)) {
        throw SessionValidationError("rdla_path is not a regular file: " + rdlaPath);
    }
    if (access(rdlaPath.c_str(), R_OK) != 0) {
        throw SessionValidationError("rdla_path is not readable: " + rdlaPath);
    }

    // Drop any previous scene before constructing the new one so a failed
    // CREATE_SCENE never leaves a half-replaced session (LIFECYCLE.md: applied
    // only when the renderer's lifecycle permits it). mOptions itself is the
    // single process-wide instance initGlobalDriver() was called with (see
    // RenderSession.h) -- only its scene-file list is mutated, matching the
    // CLI's own reuse of one RenderOptions across renders.
    mRenderContext.reset();
    mOptions.setSceneFiles(std::vector<std::string>{rdlaPath});

    std::stringstream initMessages;
    auto ctx = std::make_unique<moonray::rndr::RenderContext>(mOptions, &initMessages);
    ctx->initialize(initMessages, moonray::rndr::RenderContext::LoggingConfiguration::ATHENA_DISABLED);
    mRenderContext = std::move(ctx);

    Json::Value result(Json::objectValue);
    result["ok"] = true;
    result["rdla_path"] = rdlaPath;
    result["init_messages"] = initMessages.str();
    return result;
}

Json::Value RenderSession::startRender(const std::string& renderMode)
{
    if (!mRenderContext) {
        throw SessionValidationError("START_RENDER received with no scene created (send CREATE_SCENE first)");
    }
    if (renderMode != "final") {
        // Progressive viewport / animation render modes are Phase 08/09 scope.
        throw UnsupportedFeatureError("render_mode '" + renderMode + "' is not implemented in Phase 04 (only 'final' is)");
    }

    const auto start = std::chrono::steady_clock::now();

    mRenderContext->setRenderMode(moonray::rndr::RenderMode::BATCH);
    mRenderContext->startFrame();
    while (!mRenderContext->isFrameComplete()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
    mRenderContext->stopFrame();

    const auto renderEnd = std::chrono::steady_clock::now();

    scene_rdl2::fb_util::RenderBuffer buffer;
    mRenderContext->snapshotRenderBuffer(&buffer, /*untile*/ true, /*parallel*/ true, /*usePrimaryAov*/ true);

    const unsigned width = buffer.getWidth();
    const unsigned height = buffer.getHeight();
    const std::size_t byteSize = static_cast<std::size_t>(width) * height * sizeof(scene_rdl2::math::Vec4f);

    // Replace any previous render's shared-memory segment for this session.
    unlinkSharedMemory(mLastShmName);
    const ShmPublishResult shm = publishToSharedMemory("/moonray_bridge_fb", buffer.getData(), byteSize);
    mLastShmName = shm.name;

    const auto publishEnd = std::chrono::steady_clock::now();

    const auto renderMs = std::chrono::duration_cast<std::chrono::milliseconds>(renderEnd - start).count();
    const auto totalMs = std::chrono::duration_cast<std::chrono::milliseconds>(publishEnd - start).count();

    Json::Value result(Json::objectValue);
    result["cancelled"] = false;
    result["width"] = width;
    result["height"] = height;
    result["channels"] = 4;
    result["dtype"] = "float32";
    result["shm_name"] = shm.name;
    result["byte_size"] = static_cast<Json::UInt64>(shm.byteSize);
    result["render_ms"] = static_cast<Json::Int64>(renderMs);
    result["total_ms"] = static_cast<Json::Int64>(totalMs);
    return result;
}

} // namespace moonray_bridge
