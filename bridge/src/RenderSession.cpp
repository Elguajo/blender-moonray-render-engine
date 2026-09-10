#include "RenderSession.h"
#include "SceneBuilder.h"
#include "SharedMemoryBuffer.h"

#include <moonray/rendering/rndr/RenderContext.h>
#include <moonray/rendering/rndr/RenderOptions.h>
#include <moonray/rendering/rndr/Types.h>
#include <scene_rdl2/common/fb_util/FbTypes.h>
#include <scene_rdl2/common/math/Vec4.h>
#include <scene_rdl2/scene/rdl2/SceneContext.h>

#include <chrono>
#include <sstream>
#include <thread>

namespace moonray_bridge {

namespace {

// Maps the two SceneBuilder validation exception types onto RenderSession's
// own (which BridgeServer/main.cpp already classifies into ERROR_MODEL
// categories 1/2) so callers only need to catch RenderSession's types.
template <typename Fn>
Json::Value runSceneBuilderCall(Fn&& fn)
{
    try {
        return fn();
    } catch (const SceneBuilderValidationError& e) {
        throw SessionValidationError(e.what());
    } catch (const SceneBuilderUnsupportedError& e) {
        throw UnsupportedFeatureError(e.what());
    }
}

} // namespace

RenderSession::RenderSession(moonray::rndr::RenderOptions& options) : mOptions(options) {}

RenderSession::~RenderSession()
{
    mRenderContext.reset();
    unlinkSharedMemory(mLastShmName);
}

Json::Value RenderSession::createScene(const Json::Value& sceneVariables)
{
    // Drop any previous scene before constructing the new one so a failed
    // CREATE_SCENE never leaves a half-replaced session (LIFECYCLE.md: applied
    // only when the renderer's lifecycle permits it). mOptions itself is the
    // single process-wide instance initGlobalDriver() was called with (see
    // RenderSession.h); Phase 06 no longer sets a scene-file list at all --
    // the RenderContext's SceneContext is built directly via SceneBuilder
    // (RenderContext::loadScene() is a no-op over an empty scene-file list,
    // confirmed against the pinned moonray source: it just sets mSceneLoaded
    // and leaves whatever SceneContext state already exists untouched).
    mRenderContext.reset();
    mOptions.setSceneFiles(std::vector<std::string>{});
    mInitialized = false;
    mHasCamera = false;

    std::stringstream initMessages;
    auto ctx = std::make_unique<moonray::rndr::RenderContext>(mOptions, &initMessages);
    runSceneBuilderCall([&] {
        buildSceneScaffold(ctx->getSceneContext(), sceneVariables);
        return Json::Value();
    });
    mRenderContext = std::move(ctx);

    Json::Value result(Json::objectValue);
    result["ok"] = true;
    return result;
}

Json::Value RenderSession::updateObject(const Json::Value& payload)
{
    if (!mRenderContext) {
        throw SessionValidationError("UPDATE_OBJECT received with no scene created (send CREATE_SCENE first)");
    }
    runSceneBuilderCall([&] {
        applyObjectUpdate(mRenderContext->getSceneContext(), payload);
        return Json::Value();
    });
    if (mInitialized) {
        mRenderContext->setSceneUpdated();
    }
    Json::Value result(Json::objectValue);
    result["ok"] = true;
    return result;
}

Json::Value RenderSession::updateCamera(const Json::Value& payload)
{
    if (!mRenderContext) {
        throw SessionValidationError("UPDATE_CAMERA received with no scene created (send CREATE_SCENE first)");
    }
    runSceneBuilderCall([&] {
        applyCameraUpdate(mRenderContext->getSceneContext(), payload);
        return Json::Value();
    });
    mHasCamera = true;
    if (mInitialized) {
        mRenderContext->setSceneUpdated();
    }
    Json::Value result(Json::objectValue);
    result["ok"] = true;
    return result;
}

Json::Value RenderSession::startRender(const std::string& renderMode)
{
    if (!mRenderContext) {
        throw SessionValidationError("START_RENDER received with no scene created (send CREATE_SCENE first)");
    }
    if (!mHasCamera) {
        throw SessionValidationError("START_RENDER received with no camera created (send UPDATE_CAMERA first)");
    }
    if (renderMode != "final") {
        // Progressive viewport / animation render modes are Phase 08/09 scope.
        throw UnsupportedFeatureError("render_mode '" + renderMode + "' is not implemented in Phase 04 (only 'final' is)");
    }

    if (!mInitialized) {
        std::stringstream initMessages;
        mRenderContext->initialize(initMessages, moonray::rndr::RenderContext::LoggingConfiguration::ATHENA_DISABLED);
        mInitialized = true;
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
