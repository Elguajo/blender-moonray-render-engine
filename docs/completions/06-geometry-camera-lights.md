# Phase 06 Completion — Geometry, Transforms, Camera and Lights Translation

Status: COMPLETED
Completed: 2026-09-11
Workstation: `DESKTOP-9O2U790`, distro `MoonRay-Rocky9` (WSL2, Rocky Linux 9.8)

## Outcome
The bridge protocol was extended from Phase 04/05's raw `.rdla`-path
`CREATE_SCENE` to a structured schema (ADR-0005): `CREATE_SCENE` now builds
an empty scene scaffold, and `UPDATE_OBJECT`/`UPDATE_CAMERA` populate it with
real RDL2 `SceneObject`s constructed natively in the bridge
(`bridge/src/SceneBuilder.cpp`), replacing ASCII round-tripping.
`addon/scene_translator.py` replaces Phase 05's one-mesh/one-light
`scene_writer.py` with a general translator: any number of mesh objects,
native Blender light-type mapping (`POINT`/`SUN`/`SPOT`/`AREA` →
`Sphere`/`Distant`/`Spot`/`Rect`/`DiskLight`), the confirmed camera
unit/convention mapping, and per-object visibility flags. Phase 05's
un-root-caused `DistantLight`/`SphereLight` lighting anomaly was root-caused
and fixed (see "Decisions made"). Verified with a real Blender
`--background` render (two mesh objects + a tilted `SUN` light) through the
actual `RenderEngine.render()` path, and a 23-check bridge-protocol smoke
test suite against the real bridge + MoonRay. See `docs/evidence/phase06/`.

## Delivered
- `bridge/src/SceneBuilder.h`/`.cpp` — JSON payload → RDL2 `SceneObject`
  construction: `buildSceneScaffold()` (SceneVariables + GeometrySet + Layer
  + LightSet + placeholder material), `applyObjectUpdate()` (mesh/light
  create/update/delete, enforcing the GeometrySet invariant below),
  `applyCameraUpdate()`.
- `bridge/src/RenderSession.h`/`.cpp` — `createScene()` now builds the
  scaffold instead of loading a file; new `updateObject()`/`updateCamera()`;
  `RenderContext::initialize()` deferred to the first `startRender()` (needs
  a camera present); later updates flow through `setSceneUpdated()`.
- `bridge/src/main.cpp` — `UPDATE_OBJECT`/`UPDATE_CAMERA` dispatch to the new
  `RenderSession` methods (previously `NOT_IMPLEMENTED_PHASE04`).
- `bridge/src/Protocol.h` — `protocol_version` 1 → 2 (breaking payload-shape
  change, per `MESSAGE_SCHEMA.md`'s own versioning rule).
- `scripts/linux/phase06_build_bridge.sh` — build script (separate `bridge06`
  build directory; Phase 04's `bridge04` evidence build untouched).
- `addon/scene_translator.py` — general Blender → structured-protocol
  translator: multi-object mesh extraction (vertices/indices/normals/UVs,
  per-object visibility), camera unit mapping, native light-type mapping
  with the orientation fix (see below), `ELLIPSE`-shape explicit failure.
  Replaces and removes `addon/scene_writer.py`.
- `addon/bridge_client.py` / `bridge/client/bridge_client.py` —
  `protocol_version` 2, `create_scene(scene_variables)`, new
  `update_object()`/`update_camera()`.
- `addon/bridge_launcher.py` — default bridge binary path updated to the
  Phase 06 build.
- `addon/engine.py` — wired to `scene_translator.write_via_bridge()`.
- `bridge/tests/run_phase06_tests.py` — 23-check smoke test suite against the
  real bridge + MoonRay (structured create+render, update+re-render,
  delete-before-first-render, unsupported-light-class rejection).
- `docs/decisions/ADR-0005-structured-scene-protocol.md`.
- `docs/bridge/SCENE_TRANSLATION.md`, `MESSAGE_SCHEMA.md`, `PROTOCOL.md` —
  updated decided/open status throughout.
- `docs/evidence/phase06/` — Blender background-mode render evidence,
  `light-orientation-fix/` root-cause investigation record.

## Observed verification
| Check | Result |
|---|---|
| Structured `CREATE_SCENE`/`UPDATE_OBJECT`/`UPDATE_CAMERA` accepted and render correctly | PASS — `bridge/tests/run_phase06_tests.py`, 23/23 checks, real bridge + MoonRay |
| `GeometrySet` invariant honored (geometry not in a `GeometrySet` never renders) | PASS by construction (`SceneBuilder.cpp` adds every mesh to both `GeometrySet` and `Layer`) and by the pre-flight source read (`docs/bridge/SCENE_TRANSLATION.md` "Mesh geometry") |
| Object update (attribute change) takes effect on the next render in a live session | PASS — moved-mesh test, center pixel goes from lit to dark |
| Object delete takes effect before the first render of a session | PASS — delete-before-first-render test, center pixel dark |
| Object delete after a render already happened in the same session | **NOT confirmed** — tried and observed to not reliably remove the geometry from a second render; documented open limitation for Phase 08, not exercised by the add-on today (one-shot bridge process per render) |
| Unsupported light class rejected explicitly, not silently mis-rendered | PASS — `ERROR` category 2 |
| Native Blender light-type mapping (`POINT`/`SUN`/`SPOT`/`AREA`→Rect/Disk) implemented, portable to Cycles/EEVEE | PASS by construction (`addon/scene_translator.py::_extract_light`); `AREA`/`ELLIPSE` fails explicitly |
| Multi-object mesh translation (more than Phase 05's exactly-one) | PASS — real Blender `--background` render, two mesh objects both visible, `docs/evidence/phase06/background-mode-multi-object-render.png` |
| A tilted (non-axis-aligned) `SUN` light illuminates correctly | PASS — same render; also isolated at the bridge level, `docs/evidence/phase06/light-orientation-fix/` |
| Per-object visibility flags (`side_type` + 9 `visible_*`) map to Blender's ray-visibility flags | Implemented (`_visibility_fields()`), not independently render-fixture-verified this phase |
| Camera framing (position/FOV) plausible for a real scene | PASS by observation (background render shows expected objects in frame); exact `film_offset`/`dof_aperture` unit scale not fixture-verified |

## Decisions made

### A. Protocol: extend to a structured schema now (ADR-0005)
See `docs/decisions/ADR-0005-structured-scene-protocol.md` for the full
reasoning, pre-flight `GeometrySet` finding, and cost tradeoff. Chosen over
continuing to write `.rdla` text, because Phase 06's own "validate
update/delete" acceptance criterion cannot be meaningfully satisfied by a
full-file rewrite, and deferring would compound the eventual protocol change
under more dependents (Phase 07 materials, Phase 08 viewport).

### B. Light mapping: native Blender types, not a MoonRay-native enum
`addon/scene_translator.py` reads Blender's own `light.type`/`light.shape`
directly (`POINT`/`SUN`/`SPOT`/`AREA` with its `SQUARE`/`RECTANGLE`/`DISK`
sub-shapes) rather than replacing Blender's light UI with a MoonRay-specific
enum, unlike `cjhosken/mfb` (`docs/research/05-prior-art-harvest.md §3.3`).
Chosen because it keeps scenes portable to Cycles/EEVEE and needs no new UI —
Blender's own `AREA` shape enum already disambiguates Rect vs. Disk.
`ELLIPSE` has no RDL2 equivalent and fails explicitly
(`SceneTranslationError`), per the phase's "fail explicitly, never silently
mis-render" acceptance criterion.

### C. SphereLight/DistantLight anomaly: root-caused and fixed
Full account: `docs/evidence/phase06/light-orientation-fix/README.md`. Every
one of `DistantLight`/`SpotLight`/`RectLight`/`DiskLight`/`SphereLight`'s
`update()` (`moonray/lib/rendering/pbr/light/*.cc`, pinned commit) composes
`node_xform` with a built-in 180-degree rotation about local X ("for
consistency with DiskLight," per that source's own comment) before deriving
the light's actual illumination direction/frame. Phase 05's translator built
`node_xform` assuming the naive "local Z = intended direction" convention,
so every `DistantLight` it emitted illuminated the mirror image (about local
X) of the intended direction — this was the real cause of both of Phase 05's
findings (SphereLight-adjacent confusion aside — see below), confirmed
against source and empirically (two independent hand-built scenes through
the unmodified Phase 04 bridge, axis-aligned and tilted, both went from flat
black to correctly lit once corrected). **This is a bug in this project's own
light-transform construction code, not a MoonRay defect** — no upstream
report filed. Phase 05's axis-snap workaround is removed entirely; the fix
is exact for arbitrary orientations. Only `DistantLight` was independently
re-rendered end-to-end; `SpotLight`/`RectLight`/`DiskLight` receive the
identical source-verified correction but were not independently re-rendered.
`SphereLight`'s *original* Phase 05 failure (with Blender-derived
position/intensity data, on this module's own geometry) was not reproduced
by a fresh, straightforward control case (light positioned above a cube,
looking down) and remains genuinely unexplained if it resurfaces with real
translated data — flagged, not claimed fixed, in the evidence README.

## Problems discovered and fixed
1. **The DistantLight/SphereLight orientation bug** — see "Decisions made" C
   above.
2. **`Mesh.calc_normals_split()` no longer exists in Blender 5.2** (removed
   upstream since split normals are computed on demand) — caught by the real
   Blender background render, not by any bridge-level test. Fixed by
   removing the call; `mesh.loops[i].normal` works without it.
3. **Wrong RDL2 attribute name for camera-ray visibility** — `visible_camera`
   used instead of the actual `visible_in_camera` (confirmed via
   `rdl2_print -c RdlMeshGeometry`), in both `SceneBuilder.cpp` and
   `scene_translator.py`. Caught by the real Blender background render
   (`NATIVE_RENDER_ERROR: No Attribute named 'visible_camera'`), not by
   `run_phase06_tests.py` (which does not exercise visibility fields).
4. **Mid-session delete-after-render does not reliably remove geometry** —
   see "Observed verification" and ADR-0005 "Costs / open follow-ups".
   Discovered by the smoke test suite itself; not a regression from working
   code, a genuine limitation found while validating the acceptance
   criterion.

## Deviations / technical debt
- Blender-power → RDL2-`intensity` unit conversion per light type is
  documented but pragmatic, not photometrically verified against a reference
  renderer (`addon/scene_translator.py::_extract_light`'s per-type
  comments) — `docs/bridge/SCENE_TRANSLATION.md` already flagged this as
  Open, and it stays open.
- Camera `horizontal_film_offset`/`vertical_film_offset` and `dof_aperture`
  unit/scale mapping is plausible (dimensional analysis) but not
  render-fixture-verified against a known-correct reference image.
- Per-object visibility flags (`_visibility_fields()`) are implemented but
  not independently render-fixture-verified.
- Mid-session delete-after-render is a known, open limitation — see above.
- `UPDATE_OBJECT`'s `attrs` map for light class-specific attributes is
  Float-only; a future non-Float attribute (e.g. an Int enum) would need a
  typed-value wrapper.
- Full `SceneObject` destruction is not implemented for `delete` — only
  `GeometrySet`/`LightSet` membership removal (see ADR-0005).
- No material/texture translation (every mesh shares one placeholder
  `DwaBaseMaterial`) — explicitly Phase 07 scope.
- GUI `F12` re-verification (as opposed to `--background` mode) was not
  independently repeated this phase; `--background` exercises the identical
  `RenderEngine.render()` code path Phase 05 established as equivalent
  evidence.

## Architectural impact
ADR-0005 added (structured scene protocol, `protocol_version` 1 → 2). ADR-
0002 (Direct Bridge primary) is unaffected. No changes to Hydra/USD (still
untouched, ADR-0002).

## GPU/XPU status carried forward
Unchanged from Phase 03/04/05: CPU is the only proven render path.

## Follow-up
Phase 07: materials/textures/instances — the placeholder-material scaffold
this phase introduced (`kDefaultMaterialName`) is the seam Phase 07 replaces
with real per-object material translation. Phase 08 should also revisit the
mid-session delete-after-render limitation before relying on it for viewport
incremental updates.
