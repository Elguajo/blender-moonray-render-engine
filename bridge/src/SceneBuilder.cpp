#include "SceneBuilder.h"

#include <scene_rdl2/scene/rdl2/rdl2.h>

#include <set>
#include <string>

namespace moonray_bridge {

using scene_rdl2::rdl2::Bool;
using scene_rdl2::rdl2::Camera;
using scene_rdl2::rdl2::Float;
using scene_rdl2::rdl2::Geometry;
using scene_rdl2::rdl2::GeometrySet;
using scene_rdl2::rdl2::Int;
using scene_rdl2::rdl2::IntVector;
using scene_rdl2::rdl2::Layer;
using scene_rdl2::rdl2::Light;
using scene_rdl2::rdl2::LightSet;
using scene_rdl2::rdl2::Mat4d;
using scene_rdl2::rdl2::Material;
using scene_rdl2::rdl2::Rgb;
using scene_rdl2::rdl2::SceneContext;
using scene_rdl2::rdl2::SceneObject;
using scene_rdl2::rdl2::Vec2f;
using scene_rdl2::rdl2::Vec2fVector;
using scene_rdl2::rdl2::Vec3f;
using scene_rdl2::rdl2::Vec3fVector;

const char* const kGeometrySetName = "bridgeGeometrySet";
const char* const kLayerName = "bridgeLayer";
const char* const kLightSetName = "bridgeLightSet";
const char* const kDefaultMaterialName = "bridgeDefaultMaterial";

namespace {

// The class-specific light attributes this bridge knows how to translate,
// per docs/bridge/SCENE_TRANSLATION.md's confirmed-from-source table -- all
// Float-typed at our pin (radius, angular_extent, cone angles, lens/aspect,
// width/height, spread), which keeps this a single generic loop instead of a
// per-class attribute dispatcher. sidedness/normalized/apply_scene_scale are
// intentionally left at their RDL2 defaults (Phase 06 scope: core Blender-
// mapped light properties, not every engine-side knob).
const std::set<std::string>& supportedLightClasses()
{
    static const std::set<std::string> kClasses = {
        "SphereLight", "DistantLight", "SpotLight", "RectLight", "DiskLight",
    };
    return kClasses;
}

const Json::Value& require(const Json::Value& payload, const char* field)
{
    if (!payload.isMember(field)) {
        throw SceneBuilderValidationError(std::string("payload missing required field '") + field + "'");
    }
    return payload[field];
}

const Json::Value& requireArray(const Json::Value& payload, const char* field)
{
    const Json::Value& v = require(payload, field);
    if (!v.isArray()) {
        throw SceneBuilderValidationError(std::string("payload field '") + field + "' must be an array");
    }
    return v;
}

Vec3f jsonToVec3(const Json::Value& v, const char* field)
{
    if (!v.isArray() || v.size() != 3) {
        throw SceneBuilderValidationError(std::string("field '") + field + "' element must be a 3-element array");
    }
    return Vec3f(v[0].asFloat(), v[1].asFloat(), v[2].asFloat());
}

Vec2f jsonToVec2(const Json::Value& v, const char* field)
{
    if (!v.isArray() || v.size() != 2) {
        throw SceneBuilderValidationError(std::string("field '") + field + "' element must be a 2-element array");
    }
    return Vec2f(v[0].asFloat(), v[1].asFloat());
}

Rgb jsonToRgb(const Json::Value& v)
{
    if (!v.isArray() || v.size() != 3) {
        throw SceneBuilderValidationError("field 'color' must be a 3-element [r, g, b] array");
    }
    return Rgb(v[0].asFloat(), v[1].asFloat(), v[2].asFloat());
}

// 16 floats, row layout vx,vy,vz,vw (each xyzw) -- matches both Mat4's own
// 16-scalar constructor and the flat layout addon/scene_translator.py already
// emits into .rdla `Mat4(...)` literals (matrix_to_rdl2_mat4/_mat4).
Mat4d jsonToMat4d(const Json::Value& v)
{
    if (!v.isArray() || v.size() != 16) {
        throw SceneBuilderValidationError("field 'transform' must be a 16-element array");
    }
    double m[16];
    for (Json::ArrayIndex i = 0; i < 16; ++i) m[i] = v[i].asDouble();
    return Mat4d(m[0], m[1], m[2], m[3],
                 m[4], m[5], m[6], m[7],
                 m[8], m[9], m[10], m[11],
                 m[12], m[13], m[14], m[15]);
}

IntVector jsonToIntVector(const Json::Value& arr)
{
    IntVector out;
    out.reserve(arr.size());
    for (const auto& e : arr) out.push_back(e.asInt());
    return out;
}

Vec3fVector jsonToVec3fVector(const Json::Value& arr, const char* field)
{
    Vec3fVector out;
    out.reserve(arr.size());
    for (const auto& e : arr) out.push_back(jsonToVec3(e, field));
    return out;
}

Vec2fVector jsonToVec2fVector(const Json::Value& arr, const char* field)
{
    Vec2fVector out;
    out.reserve(arr.size());
    for (const auto& e : arr) out.push_back(jsonToVec2(e, field));
    return out;
}

// docs/bridge/SCENE_TRANSLATION.md "Per-object visibility contract" (source-
// verified: Geometry.cc side_type default TWO_SIDED=0, nine visible_*
// defaulting true). Only overridden when the payload explicitly carries a
// field -- otherwise the RDL2 default applies, so a translator that omits
// these entirely still gets sane behavior.
void applyVisibility(SceneObject* obj, const Json::Value& payload)
{
    if (payload.isMember("side_type")) {
        obj->set<Int>("side_type", payload["side_type"].asInt());
    }
    static const char* const kVisibilityFlags[] = {
        "visible_in_camera",
        "visible_shadow",
        "visible_diffuse_reflection",
        "visible_diffuse_transmission",
        "visible_glossy_reflection",
        "visible_glossy_transmission",
        "visible_mirror_reflection",
        "visible_mirror_transmission",
        "visible_volume",
    };
    for (const char* flag : kVisibilityFlags) {
        if (payload.isMember(flag)) {
            obj->set<Bool>(flag, payload[flag].asBool());
        }
    }
}

SceneObject* getRequiredObject(SceneContext& ctx, const std::string& name)
{
    if (!ctx.sceneObjectExists(name)) {
        throw SceneBuilderValidationError("no such scene object: " + name);
    }
    return ctx.getSceneObject(name);
}

void applyMeshUpdate(SceneContext& ctx, const std::string& op, const std::string& name, const Json::Value& payload)
{
    if (op == "delete") {
        if (!ctx.sceneObjectExists(name)) return; // idempotent delete
        SceneObject* obj = getRequiredObject(ctx, name);
        Geometry* geom = obj->asA<Geometry>();
        if (!geom) {
            throw SceneBuilderValidationError("scene object '" + name + "' exists but is not a Geometry");
        }
        SceneObject* geomSetObj = getRequiredObject(ctx, kGeometrySetName);
        geomSetObj->beginUpdate();
        geomSetObj->asA<GeometrySet>()->remove(geom);
        geomSetObj->endUpdate();
        // Full deleteSceneObject() also requires proving the object has no
        // remaining Layer assignment (SceneContext.h: "Callers must ensure no
        // other objects still reference the deleted object ... e.g. remove it
        // from GeometrySets, LightSets, and Layers first") and Layer.h
        // exposes no unassign() at our pin -- removing GeometrySet membership
        // alone is sufficient to drop the geometry from the render (the
        // GeometrySet invariant this phase's pre-flight confirmed), so full
        // object destruction is deliberately deferred past Phase 06.
        return;
    }

    SceneObject* obj = ctx.createSceneObject("RdlMeshGeometry", name);
    Geometry* geom = obj->asA<Geometry>();
    if (!geom) {
        throw SceneBuilderValidationError("scene object '" + name + "' exists as a different, non-Geometry class");
    }

    obj->beginUpdate();
    obj->set<Mat4d>("node_xform", jsonToMat4d(require(payload, "transform")));
    obj->set<IntVector>("vertices_by_index", jsonToIntVector(requireArray(payload, "vertices_by_index")));
    obj->set<IntVector>("face_vertex_count", jsonToIntVector(requireArray(payload, "face_vertex_count")));
    obj->set<Vec3fVector>("vertex_list_0", jsonToVec3fVector(requireArray(payload, "vertex_list"), "vertex_list"));
    // pitfall (docs/research/05-prior-art-harvest.md §4 #3): RdlMeshGeometry's
    // own default is is_subd=true -- a depsgraph-evaluated Blender mesh is
    // already a polygon mesh, so this must always be forced false here.
    obj->set<Bool>("is_subd", false);
    if (payload.isMember("uv_list") && payload["uv_list"].isArray() && !payload["uv_list"].empty()) {
        obj->set<Vec2fVector>("uv_list", jsonToVec2fVector(payload["uv_list"], "uv_list"));
    }
    if (payload.isMember("normal_list") && payload["normal_list"].isArray() && !payload["normal_list"].empty()) {
        obj->set<Vec3fVector>("normal_list", jsonToVec3fVector(payload["normal_list"], "normal_list"));
    }
    applyVisibility(obj, payload);
    obj->endUpdate();

    // GeometrySet invariant (see SceneBuilder.h docstring): membership here is
    // what actually makes the geometry reach the BVH, not the Layer alone.
    SceneObject* geomSetObj = getRequiredObject(ctx, kGeometrySetName);
    geomSetObj->beginUpdate();
    geomSetObj->asA<GeometrySet>()->add(geom);
    geomSetObj->endUpdate();

    SceneObject* layerObj = getRequiredObject(ctx, kLayerName);
    SceneObject* matObj = getRequiredObject(ctx, kDefaultMaterialName);
    SceneObject* lightSetObj = getRequiredObject(ctx, kLightSetName);
    layerObj->beginUpdate();
    layerObj->asA<Layer>()->assign(geom, "", matObj->asA<Material>(), lightSetObj->asA<LightSet>());
    layerObj->endUpdate();
}

void applyLightUpdate(SceneContext& ctx, const std::string& op, const std::string& name, const Json::Value& payload)
{
    if (op == "delete") {
        if (!ctx.sceneObjectExists(name)) return; // idempotent delete
        SceneObject* obj = getRequiredObject(ctx, name);
        Light* light = obj->asA<Light>();
        if (!light) {
            throw SceneBuilderValidationError("scene object '" + name + "' exists but is not a Light");
        }
        SceneObject* lightSetObj = getRequiredObject(ctx, kLightSetName);
        lightSetObj->beginUpdate();
        lightSetObj->asA<LightSet>()->remove(light);
        lightSetObj->endUpdate();
        return;
    }

    const std::string lightClass = require(payload, "light_class").asString();
    if (supportedLightClasses().find(lightClass) == supportedLightClasses().end()) {
        // ERROR_MODEL category 2 / phase acceptance criteria: unsupported
        // light types fail explicitly, never silently mis-render.
        throw SceneBuilderUnsupportedError("unsupported light_class: " + lightClass);
    }

    SceneObject* obj = ctx.createSceneObject(lightClass, name);
    Light* light = obj->asA<Light>();
    if (!light) {
        throw SceneBuilderValidationError("scene object '" + name + "' exists as a different, non-Light class");
    }

    obj->beginUpdate();
    obj->set<Mat4d>("node_xform", jsonToMat4d(require(payload, "transform")));
    obj->set<Rgb>("color", jsonToRgb(require(payload, "color")));
    obj->set<Float>("intensity", require(payload, "intensity").asFloat());
    if (payload.isMember("attrs")) {
        const Json::Value& attrs = payload["attrs"];
        if (!attrs.isObject()) {
            throw SceneBuilderValidationError("field 'attrs' must be a JSON object");
        }
        for (auto it = attrs.begin(); it != attrs.end(); ++it) {
            obj->set<Float>(it.key().asString(), it->asFloat());
        }
    }
    obj->endUpdate();

    SceneObject* lightSetObj = getRequiredObject(ctx, kLightSetName);
    lightSetObj->beginUpdate();
    lightSetObj->asA<LightSet>()->add(light);
    lightSetObj->endUpdate();
}

} // namespace

void buildSceneScaffold(SceneContext& ctx, const Json::Value& sceneVariables)
{
    SceneObject& variables = ctx.getSceneVariables();
    variables.beginUpdate();
    if (sceneVariables.isMember("image_width")) {
        variables.set<Int>("image_width", sceneVariables["image_width"].asInt());
    }
    if (sceneVariables.isMember("image_height")) {
        variables.set<Int>("image_height", sceneVariables["image_height"].asInt());
    }
    if (sceneVariables.isMember("pixel_samples")) {
        variables.set<Int>("pixel_samples", sceneVariables["pixel_samples"].asInt());
    }
    variables.endUpdate();

    SceneObject* geomSetObj = ctx.createSceneObject("GeometrySet", kGeometrySetName);
    SceneObject* layerObj = ctx.createSceneObject("Layer", kLayerName);
    SceneObject* lightSetObj = ctx.createSceneObject("LightSet", kLightSetName);
    ctx.createSceneObject("DwaBaseMaterial", kDefaultMaterialName);

    // Explicitly set rather than relying on SceneVariables::getLayer()'s
    // "grab the first Layer we find" fallback (source-verified at our pin) --
    // correct either way with exactly one Layer, but explicit is safer once
    // Phase 07 might introduce more than one.
    variables.beginUpdate();
    variables.set("layer", layerObj);
    variables.endUpdate();

    (void)geomSetObj;
    (void)lightSetObj;
}

void applyObjectUpdate(SceneContext& ctx, const Json::Value& payload)
{
    const std::string op = require(payload, "op").asString();
    if (op != "create" && op != "update" && op != "delete") {
        throw SceneBuilderValidationError("payload field 'op' must be one of create/update/delete, got: " + op);
    }
    const std::string kind = op == "delete" && !payload.isMember("kind")
        ? std::string() // delete may omit 'kind'; both mesh/light delete paths are tried below
        : require(payload, "kind").asString();
    const std::string name = require(payload, "name").asString();

    if (op == "delete" && kind.empty()) {
        // Try both; each is a harmless no-op if the object isn't of that kind.
        if (ctx.sceneObjectExists(name)) {
            SceneObject* obj = ctx.getSceneObject(name);
            if (obj->asA<Geometry>()) {
                applyMeshUpdate(ctx, op, name, payload);
                return;
            }
            if (obj->asA<Light>()) {
                applyLightUpdate(ctx, op, name, payload);
                return;
            }
        }
        return; // already absent
    }

    if (kind == "mesh") {
        applyMeshUpdate(ctx, op, name, payload);
    } else if (kind == "light") {
        applyLightUpdate(ctx, op, name, payload);
    } else {
        throw SceneBuilderValidationError("payload field 'kind' must be 'mesh' or 'light', got: " + kind);
    }
}

void applyCameraUpdate(SceneContext& ctx, const Json::Value& payload)
{
    const std::string name = require(payload, "name").asString();
    SceneObject* obj = ctx.createSceneObject("PerspectiveCamera", name);
    Camera* camera = obj->asA<Camera>();
    if (!camera) {
        throw SceneBuilderValidationError("scene object '" + name + "' exists as a different, non-Camera class");
    }

    obj->beginUpdate();
    obj->set<Mat4d>("node_xform", jsonToMat4d(require(payload, "transform")));
    obj->set<Float>("focal", require(payload, "focal").asFloat());
    obj->set<Float>("film_width_aperture", require(payload, "film_width_aperture").asFloat());
    obj->set<Float>("horizontal_film_offset", payload.get("horizontal_film_offset", 0.0).asFloat());
    obj->set<Float>("vertical_film_offset", payload.get("vertical_film_offset", 0.0).asFloat());
    obj->set<Float>("pixel_aspect_ratio", payload.get("pixel_aspect_ratio", 1.0).asFloat());
    obj->set<Float>("near", require(payload, "near").asFloat());
    obj->set<Float>("far", require(payload, "far").asFloat());
    if (payload.get("dof", false).asBool()) {
        obj->set<Bool>("dof", true);
        obj->set<Float>("dof_aperture", require(payload, "dof_aperture").asFloat());
        obj->set<Float>("dof_focus_distance", require(payload, "dof_focus_distance").asFloat());
    }
    obj->endUpdate();

    SceneObject& variables = ctx.getSceneVariables();
    variables.beginUpdate();
    variables.set("camera", obj);
    variables.endUpdate();
}

} // namespace moonray_bridge
