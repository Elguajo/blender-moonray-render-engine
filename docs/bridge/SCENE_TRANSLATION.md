# Scene Translation Contract

Status: **TARGET DESIGN, not an implementation claim.** See [PROTOCOL.md](PROTOCOL.md) for
status conventions. Authoritative scope/acceptance for each mapping lives in the
corresponding Roadmap phase (`docs/phases/06-geometry-camera-lights.md`,
`docs/phases/07-materials-textures-instances.md`); this document is the contract those
phases implement against, not a replacement for their acceptance criteria.

## RDL2 target model (decided — this is what the bridge writes into)
Per `docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md`:
- The bridge owns one `scene_rdl2::rdl2::SceneContext`, containing named `SceneObject`s.
- Each `SceneObject` belongs to a `SceneClass` (`Camera`, `Geometry`, `Light`, `Material`,
  `Map`, ...) that declares its typed, named attributes.
- Attribute writes must be bracketed by `SceneObject::beginUpdate()` /
  `endUpdate()` — this is an RDL2 API requirement, not a bridge convention.
- Attribute set/get is most efficiently done via a class's static `AttributeKey<T>`, not
  string lookup — relevant once the bridge's C++ translation layer exists (Phase 06+).
- `SceneObject`-valued attributes (e.g. a light's `geometry` reference) hold references to
  other scene objects and default to null.

## General pipeline shape
```text
Blender source data
        ↓  (Python, depsgraph-evaluated)
canonical bridge scene message   (this contract)
        ↓  (bridge, native)
RDL2 SceneObject(s) in SceneContext
        ↓
MoonRay RenderContext
```

## Mesh geometry
```text
Blender Mesh (object.evaluated_get(depsgraph).to_mesh())
→ evaluated depsgraph mesh (post-modifier vertices/loops/polygons/normals/UVs)
→ bridge MeshMessage  (Open — Phase 04/06: exact field layout)
→ RDL2 polygon-mesh primitive, built via createPolygonMesh()
  + PrimitiveAttributeTable (per-vertex/per-face/per-facevarying attributes: uv, normal, Cd, ...)
  + LayerAssignmentId (geometry/partName/material/lightSet combination)
```
Grounded in `.../shaders/geometry-procedurals.md` (`createPolygonMesh`,
`PrimitiveAttributeTable`, `LayerAssignmentId`). The bridge is not writing a geometry
*procedural* DSO — it constructs primitives through the equivalent RDL2 geometry object.
**Confirmed** against `moonray` source at the commit pinned in `UPSTREAM_LOCK.json`
(`eef67ae9...`): the built-in class is `RdlMeshGeometry`
(`dso/geometry/RdlMesh/RdlMeshGeometry.cc`); the same directory ships
`polymesh2rdlmesh.py` as prior art for a Python-side mesh-to-RDL2 exporter. Sibling
built-ins confirmed in `dso/geometry/`: `RdlCurve`, `RdlInstancerGeometry`, `RdlPoint`,
`Vdb`.

## Transforms
```text
Blender object.matrix_world
→ RDL2 Node::node_xform attribute (Mat4d)
```
Every RDL2 `Node` subclass (`Camera`, `Geometry`, `Light`, ...) carries `node_xform`
(`scene_rdl2-library.md`). Coordinate-system/unit-convention validation is explicit Phase 06
scope ("Validate coordinate systems/unit conventions" — `docs/phases/06-geometry-camera-lights.md`);
do not assume Blender's Z-up/meters convention needs no conversion until that phase produces
evidence.

## Camera
```text
Blender Camera object + camera data (lens, sensor, clip start/end, DOF)
→ RDL2 PerspectiveCamera (or OrthographicCamera / SphericalCamera as applicable)
  - focal                  ← lens (mm)
  - near / far             ← clip_start / clip_end
  - dof / dof_aperture /
    dof_focus_distance     ← depth-of-field settings
  - film_width_aperture,
    horizontal/vertical_film_offset,
    pixel_aspect_ratio     ← sensor fit / shift / aspect
  - node_xform             ← matrix_world
```
**Confirmed** against `moonray` source at the pinned commit (`eef67ae9...`).
`dso/camera/` ships six built-ins: `PerspectiveCamera`, `OrthographicCamera`,
`SphericalCamera`, `BakeCamera`, `DomeMaster3DCamera`, `FisheyeCamera` — Blender's stock
camera types (Perspective/Orthographic/Panoramic) map onto the first two plus
`SphericalCamera`/`FisheyeCamera` for panoramic sub-types; the others have no Blender
built-in source and are out of scope unless a future requirement adds them.

Attribute names confirmed from `dso/camera/PerspectiveCamera/attributes.cc` and the base
`Camera` class in `scene_rdl2` (`lib/scene/rdl2/Camera.cc`):
- Base `Camera` (all camera classes): `near`, `far`, `mb_shutter_open`, `mb_shutter_close`,
  `mb_shutter_bias`, `pixel_sample_map`, `medium_material`, `medium_geometry`.
- `PerspectiveCamera`-specific: `focal`, `film_width_aperture`, `horizontal_film_offset`,
  `vertical_film_offset`, `pixel_aspect_ratio`, `dof`, `dof_aperture`,
  `dof_focus_distance`, `bokeh`/`bokeh_sides`/`bokeh_image`/`bokeh_angle`/
  `bokeh_weight_location`/`bokeh_weight_strength`, `stereo_view`,
  `stereo_interocular_distance`, `stereo_convergence_distance`.

Exact Blender-field-to-RDL2-attribute unit/convention mapping (e.g. `lens` mm vs. `focal`,
sensor-fit vs. `film_width_aperture`) is still **Open — Phase 06**, since it requires
render-fixture verification, not just attribute-name matching.

## Lights
```text
Blender Light object (type: POINT / SUN / SPOT / AREA)
→ RDL2 Light subclass  (Open — Phase 06: exact Blender-type → RDL2-class mapping)
  - node_xform          ← matrix_world
  - color / intensity / exposure / camera-visibility / shadowing
    (common to every rdl2::Light per shaders/lights.md)
```
`.../shaders/lights.md` confirms `SphereLight` and `CylinderLight` exist and share a common
`rdl2::Light` attribute base (color, intensity, exposure, camera visibility, shadowing). It
does **not** enumerate the full shipped light set — do not assume Blender's Sun/Area/Spot map
1:1 onto specific RDL2 classes until Phase 06 confirms the actual class list from MoonRay
source or upstream user-reference docs. Unsupported light types must fail/fall back
explicitly, never silently mis-render (`docs/phases/06-geometry-camera-lights.md` acceptance
criteria).

## Materials
```text
Blender Principled BSDF (+ supported node subset)
→ normalized intermediate material representation   (Open — Phase 07: exact schema)
→ MoonRay Material shader configured via BsdfBuilder
  (BsdfComponents such as MicrofacetIsotropicBRDF, LambertianBRDF, ...)
```
Grounded in `.../shaders/materials.md`: MoonRay materials are not authored as flat
attribute-to-attribute maps but as an ordered set of `BsdfComponent`s added through
`BsdfBuilder`, which handles weighting/Fresnel/energy conservation. A **DwaBase-family
standard shader** is the working assumption for MoonRay's production entry point for a
Principled-like material, but no vendored developer-reference page documents its exact class
name or attribute set — that page covers *writing new* shaders, not the shipped standard
library. **Exact target class + attribute mapping is
Open — Phase 07** and must be confirmed against MoonRay source headers or upstream
user-reference docs before being asserted as supported, per the "never infer support solely
from documentation" rule in `CLAUDE.md`. Phase 07 must also produce an explicit
supported-node support matrix; unsupported nodes are surfaced explicitly, never silently
dropped.

## Textures
```text
Blender Image Texture node (+ UV Map input)
→ RDL2 ImageMap bound to a bindable material attribute
```
Per `scene_rdl2-library.md`: bindable attributes have both a value and an optional `Map`
binding; a bound `Map` produces a single RGB output (r,g,b map to Vec3 elements 0,1,2; Float
attributes take the r/g/b average). Default attribute values are often `0`/`(0,0,0)` and may
need to be reset to `1`/`(1,1,1)` once a binding is applied, since the stored value acts as a
multiplier. Texture reload/invalidation semantics are Phase 07 scope.

## Instancing
```text
Blender object/collection instances (duplis, particle instancing, collection instances)
→ RDL2 instancer geometry referencing a shared prototype
  (RdlInstancerGeometry, per shaders/geometry-procedurals.md)
```
Whether native MoonRay instancing is used or instances are expanded is a Phase 07 decision
gated on "Instances do not expand unexpectedly when native instancing is supported/selected"
(`docs/phases/07-materials-textures-instances.md`).

## Update / delete semantics
```text
Blender depsgraph change (add / modify / remove)
→ change classification (bridge)
→ RDL2 attribute update inside beginUpdate()/endUpdate(), or SceneObject removal
→ applied only when MoonRay's render lifecycle permits (see LIFECYCLE.md)
```
RDL2 supports delta-only serialization (`writeSceneToFile(..., deltaEncoding=true)` writes
only attributes changed since the last `commitAllChanges()`) — this is the mechanism Arras
clients use for incremental sends and is the natural basis for bridge incremental updates,
but the bridge's own wire-level update protocol is **Open — Phase 06.**

## Decided vs. open summary
| Mapping | Status |
|---|---|
| RDL2 `SceneContext`/`SceneObject`/`SceneClass`/`Attribute` as the target data model | **Decided** (RDL2 API, not a project choice) |
| `node_xform` carries world transform for every `Node` subclass | **Decided** (RDL2 API) |
| Mesh → `createPolygonMesh` + `PrimitiveAttributeTable` + `LayerAssignmentId` | **Decided shape**, exact bridge message layout **Open — Phase 04/06** |
| Blender light type → specific RDL2 light class | **Open — Phase 06** |
| Camera attribute set beyond focal/near/far | **Open — Phase 06** |
| Principled BSDF → specific MoonRay material class/attributes | **Open — Phase 07** |
| Supported-node matrix (materials) | **Open — Phase 07**, mandatory before claiming support |
| Instancing: native vs. expanded | **Open — Phase 07** |
| Incremental update wire protocol | **Open — Phase 06** |
