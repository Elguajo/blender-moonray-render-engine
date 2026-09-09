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
→ RDL2 Light subclass
  - node_xform          ← matrix_world
  - color / intensity / exposure / camera-visibility / shadowing
    (common to every rdl2::Light per shaders/lights.md)
```
**Confirmed** against `moonray` source at the pinned commit (`eef67ae9...`): `dso/light/`
ships nine built-ins — `SphereLight`, `DiskLight`, `DistantLight`, `SpotLight`, `RectLight`,
`CylinderLight`, `EnvLight`, `MeshLight`, `PortalLight` — each sharing the common
`rdl2::Light` base (color, intensity, exposure, camera visibility, shadowing) plus these
confirmed class-specific attributes (from each DSO's `attributes.cc`):

| RDL2 class | Key attributes | Proposed Blender source |
|---|---|---|
| `SphereLight` | `radius`, `sidedness`, `normalized`, `apply_scene_scale` | `POINT` |
| `DistantLight` | `angular_extent`, `normalized` | `SUN` |
| `SpotLight` | `inner_cone_angle`, `outer_cone_angle`, `angle_falloff_type`, `lens_radius`, `aspect_ratio`, `focal_plane_distance`, `black_level` | `SPOT` |
| `RectLight` | `width`, `height`, `spread`, `sidedness` | `AREA` (shape = `SQUARE`/`RECTANGLE`) |
| `DiskLight` | `radius`, `spread`, `sidedness` | `AREA` (shape = `DISK`) |
| `CylinderLight` | `radius`, `height`, `sidedness` | no direct Blender light-type source |
| `EnvLight` | (environment/dome) | World background, if mapped at all |
| `MeshLight` | `geometry` (`SceneObject*` reference to the emitting geometry) | emissive-material mesh objects |
| `PortalLight` | (env-light portal) | no direct Blender light-type source |

This table **replaces the earlier "class list unconfirmed" caveat** — the class names and
attributes above are read directly from source, not inferred from the plugin-authoring
guide. What remains **Open — Phase 06** is the actual mapping *decision* and its
render-fixture verification, in particular:
- Blender's `AREA` light has a fourth shape, `ELLIPSE`, with no matching RDL2 primitive —
  must fail/fall back explicitly rather than silently substitute `DiskLight`/`RectLight`.
- Unit/value-scale conversion per attribute (e.g. Blender's radiometric power vs. RDL2
  `intensity`/`exposure`/`normalized`).
- Whether `CylinderLight`/`PortalLight` are exposed at all in the first supported set, since
  Blender has no built-in light type that maps onto them directly.

Unsupported light types must fail/fall back explicitly, never silently mis-render
(`docs/phases/06-geometry-camera-lights.md` acceptance criteria).

## Materials
```text
Blender Principled BSDF (+ supported node subset)
→ normalized intermediate material representation   (Open — Phase 07: exact schema)
→ MoonRay Material shader (DwaBaseMaterial or UsdPreviewSurface — see below),
  itself implemented internally via BsdfBuilder / BsdfComponents
  (MicrofacetIsotropicBRDF, LambertianBRDF, ...) — the bridge targets the
  Material's declared attributes, not the BsdfBuilder API directly.
```
Grounded in `.../shaders/materials.md`: a MoonRay Material shader's C++ implementation
configures a `BsdfBuilder`, but the bridge (an RDL2 client, not a shader author) only ever
sets the Material *scene object's* declared attributes — it does not call `BsdfBuilder`
itself. Two confirmed candidate target classes, checked directly against source rather than
inferred from the plugin-authoring guide:

**`DwaBaseMaterial`** — confirmed to exist at `dso/material/DwaBase/DwaBaseMaterial.json` in
the separate **`moonshine`** repository (not `moonray`/`scene_rdl2` core; pinned in
`UPSTREAM_LOCK.json` as of this check). This is DreamWorks' production shading model —
`interface_flags: INTERFACE_DWABASELAYERABLE`, attribute set assembled from ~17 included
JSON fragments (fuzz, clearcoat, glitter, specular, refractive_index, metallic, roughness,
anisotropy, iridescence, diffuse, subsurface, diffuse_transmission, transmission, normal,
misc, emission). Confirmed key attributes: `albedo` (Rgb, base color), `roughness` (Float),
`metallic` (Float, 0/1 toggle) + `metallic_color`/`metallic_edge_color`, `specular` (Float) +
`refractive_index` (Float, default 1.5), `transmission` (Float toggle) +
`transmission_color`, `emission` (Rgb) + `show_emission` (Bool), `input_normal`. Using it
requires vendoring/building `moonshine` in addition to `moonray`/`scene_rdl2` — a real
dependency-surface increase not required by any phase before Phase 07.

**`UsdPreviewSurface`** — confirmed to exist at
`dso/material/UsdPreviewSurface/UsdPreviewSurface.json` inside **`moonray` core itself**
(already pinned, no extra repo). Confirmed attributes: `diffuseColor` (Rgb, default
0.18 — note: linear-grey default, not Blender's 0.8), `emissiveColor`, `useSpecularWorkflow`
(Bool), `specularColor`, `metallic` (Float), `roughness` (Float, default 0.5), `clearcoat`,
`clearcoatRoughness`, `opacity`, `opacityThreshold`, `ior` (default 1.5), `normal` (Vec3f),
`displacement`, `occlusion`. This is a near-1:1 structural match to Blender's Principled
BSDF's core fields (base color / metallic / roughness / IOR / clearcoat / normal / opacity)
and ships with the dependency set already required from Phase 03 onward.

**This is a real Phase 07 tradeoff, not yet decided:** `DwaBaseMaterial` is the more
production-complete shading model (fuzz, subsurface, diffuse transmission, iridescence,
independent transmission IOR/roughness — none of which `UsdPreviewSurface` exposes) at the
cost of a second vendored/built upstream repo; `UsdPreviewSurface` is lower-risk and
structurally closer to Principled BSDF's field set but has a materially smaller feature
surface (no subsurface, no fuzz/iridescence, single shared IOR for reflection+transmission).
Phase 07 must make and record this choice (or a hybrid — e.g. `UsdPreviewSurface` first,
`DwaBaseMaterial` as a later opt-in) with an ADR if the decision is consequential enough,
per `CLAUDE.md`'s decision-worthy criteria. It must also produce an explicit supported-node
support matrix regardless of target class; unsupported nodes are surfaced explicitly, never
silently dropped.

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
| Mesh target class is `RdlMeshGeometry` | **Confirmed** (source-checked); bridge message layout **Open — Phase 04/06** |
| Camera/light built-in class names + confirmed attribute lists | **Confirmed** (source-checked) |
| Blender light type → specific RDL2 light class | **Proposed** (table above); render-fixture verification **Open — Phase 06** |
| Camera field unit/convention mapping (lens↔focal, sensor fit, etc.) | **Open — Phase 06** |
| `DwaBaseMaterial` vs. `UsdPreviewSurface` as the Principled BSDF target | **Confirmed both exist** (source-checked); **choice is Open — Phase 07** |
| Principled BSDF → chosen material class's exact attribute mapping | **Open — Phase 07** |
| Supported-node matrix (materials) | **Open — Phase 07**, mandatory before claiming support |
| Instancing: native vs. expanded | **Open — Phase 07** |
| Incremental update wire protocol | **Open — Phase 06** |
