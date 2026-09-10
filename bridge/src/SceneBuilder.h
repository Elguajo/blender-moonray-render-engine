// Phase 06: structured JSON payload -> RDL2 SceneObject construction. This is
// the native counterpart to docs/bridge/SCENE_TRANSLATION.md's canonical
// bridge scene schema (ADR-0005) -- it replaces Phase 04/05's raw .rdla-path
// CREATE_SCENE with real scene_rdl2 API calls (SceneContext::createSceneObject
// + SceneObject::set, bracketed by beginUpdate()/endUpdate() as the API
// requires).
//
// GeometrySet invariant (docs/bridge/SCENE_TRANSLATION.md "Mesh geometry",
// source-verified against moonray/lib/rendering/rt/GeometryManager.cc): a
// Geometry not added to the fixed GeometrySet never reaches the BVH even if
// it is assigned in the Layer. Every mesh create here adds it to both.
#pragma once

#include <json/json.h>

#include <stdexcept>
#include <string>

namespace scene_rdl2 {
namespace rdl2 {
class SceneContext;
}
}

namespace moonray_bridge {

// Thrown for a structurally invalid UPDATE_OBJECT/UPDATE_CAMERA/CREATE_SCENE
// payload (missing/mistyped field) -- caller maps this to ERROR_MODEL
// category 1, mirroring RenderSession's SessionValidationError.
class SceneBuilderValidationError : public std::runtime_error {
public:
    explicit SceneBuilderValidationError(const std::string& msg) : std::runtime_error(msg) {}
};

// Thrown for a well-formed payload that names an unsupported light class --
// ERROR_MODEL category 2 ("fail explicitly, never silently mis-render", per
// docs/phases/06-geometry-camera-lights.md acceptance criteria).
class SceneBuilderUnsupportedError : public std::runtime_error {
public:
    explicit SceneBuilderUnsupportedError(const std::string& msg) : std::runtime_error(msg) {}
};

// Fixed names for the single GeometrySet/Layer/LightSet/placeholder material
// every Phase 06 scene uses. Multi-material/per-object assignment is Phase 07
// scope (docs/bridge/SCENE_TRANSLATION.md "Materials" is Open -- Phase 07);
// until then every mesh shares kDefaultMaterialName.
extern const char* const kGeometrySetName;
extern const char* const kLayerName;
extern const char* const kLightSetName;
extern const char* const kDefaultMaterialName;

// CREATE_SCENE (structured, Phase 06 payload): builds SceneVariables fields
// (image_width/image_height/pixel_samples) and the fixed GeometrySet/Layer/
// LightSet/default-material scaffold in a freshly constructed, otherwise-
// empty SceneContext (RenderContext's own mSceneContext right after
// construction, before initialize() is called).
void buildSceneScaffold(scene_rdl2::rdl2::SceneContext& ctx, const Json::Value& sceneVariables);

// UPDATE_OBJECT: create/update/delete one mesh or light SceneObject.
// payload.op in {"create", "update", "delete"}; "update" and "create" are
// handled identically (createSceneObject() returns the existing object if
// name+class already match, matching scene_rdl2's own documented semantics),
// so both fully re-specify the object's attributes each call -- partial
// (sparse) update is not Phase 06 scope.
void applyObjectUpdate(scene_rdl2::rdl2::SceneContext& ctx, const Json::Value& payload);

// UPDATE_CAMERA: create/update the scene's single camera (Phase 06 supports
// exactly one, matching Blender's single active-camera-per-render model) and
// point SceneVariables.camera at it.
void applyCameraUpdate(scene_rdl2::rdl2::SceneContext& ctx, const Json::Value& payload);

} // namespace moonray_bridge
