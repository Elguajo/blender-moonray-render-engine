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

**Confirmed against pinned source (Phase 06 pre-flight, 2026-09-10), superseding the earlier
"reported, not yet source-verified" note from OpenMoonRay discussion #223:** a `Geometry`
object must be a member of at least one `GeometrySet` in the `SceneContext` to actually
appear in the render — **Layer assignment alone is not sufficient.**

Evidence, read directly from source at the commits pinned in `UPSTREAM_LOCK.json` (not from
docs, not from discussion #223):
- `scene_rdl2` `lib/scene/rdl2/GeometrySet.h`/`.cc` (`1229d3ea...`): a `GeometrySet` is a
  `SceneObject` holding one attribute, `geometries` (`SceneObjectIndexable`), with
  `add()`/`remove()`/`contains()` convenience methods. Nothing here alone proves it is
  render-mandatory — that requires tracing who actually reads it.
- `moonray` `lib/rendering/rt/GeometryManager.cc` (`eef67ae9...`) is where it becomes
  mandatory. `GeometryManager::finalizeChange()` (the BVH-build entry point used for a full
  scene build, `ChangeFlag::ALL`) calls `mSceneContext->getAllGeometrySets()` to obtain the
  `GeometrySetVector` it hands to `collectPrimitives()`. `collectPrimitives()` (`:819-861`)
  iterates **only** `for (auto& geometrySet : geometrySets) { ... geometrySet->getGeometries() ...}`
  — i.e. it visits geometry exclusively by walking `GeometrySet` membership. For each geometry
  found this way it then checks `g2s.find(geom)` (the Layer's `GeometryToRootShadersMap`) and
  skips it if the Layer never assigned it — so Layer assignment is a *necessary filter inside*
  the GeometrySet walk, not an alternate way to reach a geometry. A `Geometry` scene object
  that is assigned in the `Layer` but is a member of **no** `GeometrySet` is never visited by
  this loop at all: its `Procedural` is never generated, never tessellated, and it is silently
  absent from the BVH and the render, with **no error, no warning, no validation failure** —
  RDL2 accepts and stores the object either way.
- `RenderContext.cc`'s two `beginGeometrySet()`/`endGeometrySet()` call sites (`:2803-2805`,
  `:2854-2856`, `reportGeometryMemory()`/`reportGeometryStatistics()`) are reporting-only and
  were not the deciding evidence — `GeometryManager.cc` is.

**Consequence for Phase 06 (load-bearing for the translation schema, not just a note):** every
`Geometry`-derived object the translator creates (mesh, and later any instancer geometry) MUST
be added to a `GeometrySet` that is itself `includeInBVH()` (default `true`) as part of the
same scene-build/update, in addition to its `Layer` assignment. Phase 05's own
`addon/scene_writer.py:335-337` already does this by construction (mirroring
`testdata/rectangle.rdla`, not because it had been source-verified) — Phase 06's canonical
schema and its incremental add/update/delete semantics must preserve this invariant
explicitly and deliberately, including on incremental adds: a newly created `Geometry` that
is assigned to the `Layer` but not yet added to the relevant `GeometrySet` in the same update
will render as if it does not exist, with no diagnostic — this is exactly the kind of silent
mis-render Phase 06's acceptance criteria ("Unsupported types fail or fall back explicitly,
never silently mis-render") is written to prevent, so add-to-GeometrySet must be treated as a
mandatory, validated step of "add a geometry object," not an optional/best-effort one.

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

**Implemented — Phase 06** (`addon/scene_translator.py::_extract_camera`): `focal` ←
`lens`; `film_width_aperture` ← `sensor_width`; `near`/`far` ← `clip_start`/`clip_end`;
`pixel_aspect_ratio` ← `scene.render.pixel_aspect_y / pixel_aspect_x` (inverted, per the
table above); `horizontal_film_offset`/`vertical_film_offset` ← `shift_x`/`shift_y *
sensor_width`; `dof`/`dof_aperture`/`dof_focus_distance` ← `use_dof`/`lens / f-stop`/
`focus_distance` (or distance-to-`focus_object`). **Camera framing itself was verified by
observation** (a real Blender-driven render, `docs/evidence/phase06/`, showed the expected
objects in frame at plausible positions) but the exact unit/scale of `film_offset` and
`dof_aperture` was **not** render-fixture-verified against a known-correct reference image —
treat those two as plausible, not confirmed, if precise framing/DoF matching matters.

## Lights
```text
Blender Light object (type: POINT / SUN / SPOT / AREA)
→ RDL2 Light subclass
  - node_xform          ← matrix_world, via light_xform_to_rdl2_mat4()
                           (NOT the same helper meshes/camera use --
                           see "Light orientation" note below)
  - color / intensity / exposure / camera-visibility / shadowing
    (common to every rdl2::Light per shaders/lights.md)
```

**Light orientation — root-caused and fixed in Phase 06**
(`docs/evidence/phase06/light-orientation-fix/`): every one of
`DistantLight`/`SpotLight`/`RectLight`/`DiskLight`/`SphereLight`'s `update()` composes
`node_xform` with a built-in 180-degree rotation about local X ("for consistency with
DiskLight", source's own comment), so the naive "`node_xform`'s local Z = intended
direction" construction Phase 05 used illuminates the mirror image about local X instead.
This was the actual cause of Phase 05's un-root-caused SphereLight/DistantLight anomaly for
every *orientation-dependent* light (DistantLight direction, SpotLight cone axis,
RectLight/DiskLight face normal) — confirmed against source and empirically (two independent
hand-built scenes through the unmodified Phase 04 bridge, axis-aligned and tilted, both went
from flat black to correctly lit once corrected). **Not a MoonRay defect** — no upstream
report warranted. `addon/scene_translator.py::light_xform_to_rdl2_mat4()` applies the fix;
Phase 05's axis-snap workaround is removed. Only `DistantLight` was independently
re-rendered end-to-end (both cases); `SpotLight`/`RectLight`/`DiskLight` get the identical
source-verified correction but were not independently re-rendered. `SphereLight`'s original
Phase 05 failure (with Blender-derived data) was not reproduced by a fresh, straightforward
control case and remains unexplained if it resurfaces — see the evidence README's "What
remains open".
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
guide.

**Decided and implemented — Phase 06** (decision B, native-type mapping;
`addon/scene_translator.py::_extract_light`): `POINT → SphereLight`, `SUN → DistantLight`,
`SPOT → SpotLight`, `AREA(SQUARE/RECTANGLE) → RectLight`, `AREA(DISK) → DiskLight`. Blender's
own `light.type`/`light.shape` are read directly (not replaced by a MoonRay-native enum, per
decision B's rationale: keeps scenes portable to Cycles/EEVEE, unlike `cjhosken/mfb`'s
approach, §3.3 of `docs/research/05-prior-art-harvest.md`). `AREA` with `shape = 'ELLIPSE'`
raises `SceneTranslationError` before any bridge call — confirmed by construction (explicit
check in `_extract_light`), not yet exercised by a render fixture with an actual ellipse
light. `CylinderLight`/`PortalLight`/`MeshLight`/`EnvLight` remain unmapped (no direct
Blender source for the first two; `MeshLight`/`EnvLight` are plausible future targets for
emissive materials/world background, out of Phase 06 scope). Unit/value-scale conversion
(Blender radiometric power → RDL2 `intensity`) uses documented pragmatic approximations
(`scene_translator.py`'s per-type comments), **not** verified against a photometrically
correct reference — SCENE_TRANSLATION.md's original "Open" note on this point still stands;
only "renders predictably, not identically to Cycles" is claimed.

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
**Decided and implemented — Phase 06** (ADR-0005): the bridge's wire-level protocol is the
structured `UPDATE_OBJECT` message with an explicit `op` field (`create`/`update`/`delete`),
not RDL2's own delta-serialization mechanism (that stays an internal RDL2/Arras concern, not
exposed on the wire). `delete` removes the object from its `GeometrySet`/`LightSet` (and is
idempotent if the object is already absent) rather than calling `SceneContext::deleteSceneObject()`
outright — that stronger operation additionally requires proving no remaining `Layer`
assignment, and `Layer.h` exposes no `unassign()` at this pin, so full object destruction is
deliberately deferred (`bridge/src/SceneBuilder.cpp::applyMeshUpdate`).

**Confirmed working, with one real limitation found:** `bridge/tests/run_phase06_tests.py`
verifies, against the real bridge + MoonRay: (a) `update` (an attribute change, e.g. moving
an already-rendered mesh) correctly takes effect on the *next* render within the same live
session; (b) `delete` correctly removes an object *before* the first render of a session. It
does **not** confirm delete after a render has already happened in the same session —
tried and observed to NOT reliably remove the geometry from a second render:
`RenderContext::startFrame()`'s `mSceneUpdated` path uses `rt::ChangeFlag::UPDATE` (not
`ALL`), and `GeometryManager`'s `UPDATE` path is additive/refresh-oriented, not proven to
shrink an already-built BVH when a `GeometrySet` member is removed. Not a blocker for Phase 06
itself (the add-on launches one fresh bridge process per render, per
`docs/bridge/LIFECYCLE.md` and `addon/bridge_launcher.py`'s one-shot-process lifecycle
decision, so this case is never hit today) — but a real, open problem for **Phase 08's**
incremental viewport to solve before mid-session object deletion can be trusted (likely
needs forcing `ChangeFlag::ALL` on any delete, or another `RenderContext` mechanism not yet
identified).

## Decided vs. open summary
| Mapping | Status |
|---|---|
| RDL2 `SceneContext`/`SceneObject`/`SceneClass`/`Attribute` as the target data model | **Decided** (RDL2 API, not a project choice) |
| `node_xform` carries world transform for every `Node` subclass | **Decided** (RDL2 API) |
| Mesh target class is `RdlMeshGeometry` | **Confirmed and implemented — Phase 06** (`bridge/src/SceneBuilder.cpp`) |
| Every rendered `Geometry` must be added to a `GeometrySet`, not just the `Layer` | **Confirmed** (source-checked, `GeometryManager.cc`) and **implemented — Phase 06** |
| Camera/light built-in class names + confirmed attribute lists | **Confirmed** (source-checked) |
| Blender light type → specific RDL2 light class | **Decided and implemented — Phase 06** (decision B, native-type mapping; `ELLIPSE` fails explicitly) |
| Light orientation (`node_xform` → actual illumination direction) | **Root-caused and fixed — Phase 06** (`docs/evidence/phase06/light-orientation-fix/`); `DistantLight` independently re-verified, Spot/Rect/Disk share the fix by construction only |
| Camera field unit/convention mapping (lens↔focal, sensor fit, etc.) | **Implemented — Phase 06**; framing verified by observation, exact `film_offset`/`dof_aperture` scale not fixture-verified |
| Structured `CREATE_SCENE`/`UPDATE_OBJECT`/`UPDATE_CAMERA` wire schema | **Decided and implemented — Phase 06** (ADR-0005), replacing the Phase 04/05 raw `.rdla`-path `CREATE_SCENE`; `protocol_version` 1→2 |
| Wire-level update/delete semantics | **Implemented and confirmed for the cases Phase 06 needs — Phase 06**; mid-session delete-after-render is a known, open limitation for Phase 08 (see above) |
| `DwaBaseMaterial` vs. `UsdPreviewSurface` as the Principled BSDF target | **Confirmed both exist** (source-checked); **choice is Open — Phase 07** |
| Principled BSDF → chosen material class's exact attribute mapping | **Open — Phase 07** |
| Supported-node matrix (materials) | **Open — Phase 07**, mandatory before claiming support |
| Instancing: native vs. expanded | **Open — Phase 07** |
