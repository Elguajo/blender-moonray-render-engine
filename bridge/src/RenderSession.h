// Owns the MoonRay RenderContext lifecycle for one bridge connection
// (docs/bridge/LIFECYCLE.md "Scene-session lifecycle"). Phase 06 replaced the
// Phase 04/05 raw .rdla-path CREATE_SCENE with the structured schema in
// docs/bridge/SCENE_TRANSLATION.md / ADR-0005: CREATE_SCENE builds an empty
// SceneContext scaffold, UPDATE_OBJECT/UPDATE_CAMERA populate it via
// SceneBuilder, and RenderContext::initialize() (which needs a camera/layer
// already present) runs lazily on the first START_RENDER, not in
// createScene(). A single synchronous BATCH render is still Phase 04/06
// scope; progressive/viewport modes remain out of scope (Phase 08).
#pragma once

#include <json/json.h>

#include <memory>
#include <stdexcept>
#include <string>

#include <moonray/rendering/rndr/RenderOptions.h>

namespace moonray {
namespace rndr {
class RenderContext;
}
}

namespace moonray_bridge {

// Thrown for a request that is well-formed but targets an unsupported Phase 04
// feature (ERROR_MODEL.md category 2), e.g. render_mode != "final".
class UnsupportedFeatureError : public std::runtime_error {
public:
    explicit UnsupportedFeatureError(const std::string& msg) : std::runtime_error(msg) {}
};

// Thrown for a request that violates payload/session-sequencing rules the caller
// should have avoided (ERROR_MODEL.md category 1), e.g. START_RENDER with no
// scene created yet, or a missing/invalid CREATE_SCENE path.
class SessionValidationError : public std::runtime_error {
public:
    explicit SessionValidationError(const std::string& msg) : std::runtime_error(msg) {}
};

// Native MoonRay/RDL2 failures surfaced after payload validation already passed
// (ERROR_MODEL.md category 3) are left as whatever scene_rdl2::except::* or
// std::exception MoonRay itself threw; the caller (BridgeServer) maps any
// exception not of the two types above to category 3.

class RenderSession {
public:
    // `options` must be the SAME RenderOptions instance already passed to
    // moonray::rndr::initGlobalDriver() (main.cpp constructs exactly one,
    // process-wide) -- mirroring moonray/cmd/raas_cmd/moonray/moonray.cc,
    // which uses a single RenderOptions for both calls. RenderSession does not
    // own it and never replaces it wholesale, only mutates it (setSceneFiles)
    // between renders, exactly as the CLI's own multi-render "-deltas" loop does.
    explicit RenderSession(moonray::rndr::RenderOptions& options);
    ~RenderSession();

    RenderSession(const RenderSession&) = delete;
    RenderSession& operator=(const RenderSession&) = delete;

    // Structured CREATE_SCENE (Phase 06, ADR-0005): constructs a fresh
    // RenderContext (dropping any previous scene) and builds the
    // SceneVariables/GeometrySet/Layer/LightSet/default-material scaffold via
    // SceneBuilder::buildSceneScaffold. Does not call RenderContext::initialize()
    // -- that happens lazily on the first startRender(), once UPDATE_OBJECT/
    // UPDATE_CAMERA have populated at least a camera.
    Json::Value createScene(const Json::Value& sceneVariables);

    // UPDATE_OBJECT: create/update/delete one mesh or light. Valid only after
    // createScene(). If the scene has already been initialize()d (a render
    // already happened), flags the change via RenderContext::setSceneUpdated()
    // so the next startRender() picks it up.
    Json::Value updateObject(const Json::Value& payload);

    // UPDATE_CAMERA: create/update the scene's single camera.
    Json::Value updateCamera(const Json::Value& payload);

    // Runs one synchronous BATCH render of the current scene and publishes the
    // resulting beauty buffer into shared memory. Returns the RENDER_COMPLETE
    // payload (width/height/channels/dtype/shm_name/byte_size/elapsed_ms).
    // Lazily calls RenderContext::initialize() on the first call.
    Json::Value startRender(const std::string& renderMode);

private:
    // RenderContext stores its RenderOptions argument by reference
    // (moonray/rendering/rndr/RenderContext.h: `RenderOptions& mOptions;`) --
    // it does not copy it. This must be the same object initGlobalDriver() was
    // called with and must outlive mRenderContext.
    moonray::rndr::RenderOptions& mOptions;
    std::unique_ptr<moonray::rndr::RenderContext> mRenderContext;
    std::string mLastShmName;
    bool mInitialized = false;
    bool mHasCamera = false;
};

} // namespace moonray_bridge
