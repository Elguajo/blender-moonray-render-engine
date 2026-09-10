// Owns the MoonRay RenderContext lifecycle for one bridge connection
// (docs/bridge/LIFECYCLE.md "Scene-session lifecycle"). Phase 04 scope only:
// full-scene load from an .rdla file (docs/bridge/SCENE_TRANSLATION.md defers the
// canonical mesh/camera/material bridge schema to Phase 04/06/07) and a single
// synchronous BATCH render. Incremental updates and progressive/viewport modes
// are out of scope (docs/phases/04-direct-bridge-prototype.md).
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

    // Validates `rdlaPath` (non-empty, exists, readable) before touching any
    // native state (ERROR_MODEL.md category 1), then loads it as the full scene.
    // Replaces any previously created scene in this session.
    Json::Value createScene(const std::string& rdlaPath);

    // Runs one synchronous BATCH render of the current scene and publishes the
    // resulting beauty buffer into shared memory. Returns the RENDER_COMPLETE
    // payload (width/height/channels/dtype/shm_name/byte_size/elapsed_ms).
    Json::Value startRender(const std::string& renderMode);

private:
    // RenderContext stores its RenderOptions argument by reference
    // (moonray/rendering/rndr/RenderContext.h: `RenderOptions& mOptions;`) --
    // it does not copy it. This must be the same object initGlobalDriver() was
    // called with and must outlive mRenderContext.
    moonray::rndr::RenderOptions& mOptions;
    std::unique_ptr<moonray::rndr::RenderContext> mRenderContext;
    std::string mLastShmName;
};

} // namespace moonray_bridge
