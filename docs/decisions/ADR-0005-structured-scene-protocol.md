# ADR-0005 — Structured scene protocol replaces raw `.rdla`-path `CREATE_SCENE`

Status: ACCEPTED
Date: 2026-09-11
Relates to: ADR-0004 (bridge IPC transport/wire format — this ADR fills in the
scene-message contract ADR-0004 deliberately left open), `docs/bridge/MESSAGE_SCHEMA.md`,
`docs/bridge/SCENE_TRANSLATION.md`, `docs/phases/06-geometry-camera-lights.md`

## Context
Phase 04/05 shipped `CREATE_SCENE{rdla_path}`: the add-on wrote a complete,
self-contained `.rdla` ASCII text file describing the whole scene and handed
the bridge a filesystem path; the bridge just called
`RenderContext::initialize()` against that file (`bridge/src/RenderSession.cpp`,
unchanged since Phase 04). `MESSAGE_SCHEMA.md`'s "Open — Phase 04/06/07" note
already flagged this as provisional and named Phase 06 as "the phase that
actually needs to extend it ... once general, incremental scene translation
is in scope" — which is exactly Phase 06's own acceptance criteria ("Validate
edit/update/delete").

The user asked for an explicit recommendation before implementation (per
`docs/research/05-prior-art-harvest.md §7` decision A), weighing:
- **Extend now**: a real structured `UPDATE_OBJECT`/`UPDATE_CAMERA` schema,
  translated directly into RDL2 `SceneObject`s by a new native bridge-side
  layer (`bridge/src/SceneBuilder.cpp`), replacing ASCII round-tripping.
- **Defer**: keep writing `.rdla` text from Python for Phase 06, and revisit
  only when Phase 08's viewport forces the issue.

## Decision
Extend now. `CREATE_SCENE` no longer takes a file path — its payload is
`{scene_variables: {image_width, image_height, pixel_samples}}` and builds an
empty `SceneVariables` + `GeometrySet` + `Layer` + `LightSet` +
placeholder-material scaffold directly in a fresh `RenderContext`'s
`SceneContext` (obtained via `RenderContext::getSceneContext()` *before*
`RenderContext::initialize()` is called — confirmed by reading
`RenderContext::loadScene()`'s source: an empty scene-file list is a clean
no-op over whatever `SceneContext` state already exists). `UPDATE_OBJECT`
(mesh or light, `op` ∈ `create`/`update`/`delete`) and `UPDATE_CAMERA`
populate it via real `scene_rdl2::rdl2::SceneObject::set<T>(name, value)`
calls, bracketed by `beginUpdate()`/`endUpdate()` as the RDL2 API requires.
`RenderContext::initialize()` itself is deferred to the first `START_RENDER`
(it needs a camera/layer already present); a later `UPDATE_OBJECT`/
`UPDATE_CAMERA` after that point calls `RenderContext::setSceneUpdated()` so
the next render picks up the change. `protocol_version` bumped 1 → 2 (a
breaking payload-shape change, per `MESSAGE_SCHEMA.md`'s own versioning
rule).

`UPDATE_MATERIAL`'s payload stays **Open — Phase 07**; this ADR does not
touch material translation.

### Why not defer
Phase 06's own acceptance criteria requires validating update/delete
semantics — through a full-file `.rdla` rewrite, "update" is indistinguishable
from "recreate the whole scene," which does not meaningfully exercise
anything except the file-loading path already proven in Phase 04. Deferring
would also compound: Phase 07 (materials) and Phase 08 (viewport, which
explicitly needs incremental updates without a full scene reload/reparse per
edit) would both then depend on the interim `.rdla`-path contract, growing
the blast radius of the eventual protocol change instead of shrinking it.

### Price paid now
A real new C++ subsystem (`bridge/src/SceneBuilder.h/.cpp`, ~455 lines) that
did not exist before — JSON payload validation, typed attribute construction
per mesh/camera/5 light classes, and the `GeometrySet`/`Layer`/`LightSet`
membership bookkeeping the pre-flight investigation below established as
mandatory. This is materially more Phase 06 scope than "keep writing `.rdla`
from Python" would have been, traded for Phase 08 not having to redo this
work under more accumulated dependents.

## Pre-flight finding this decision depends on
Before any of the above was implemented, `docs/bridge/SCENE_TRANSLATION.md`'s
"reported, not yet source-verified" `GeometrySet` question (research harvest
§4 #11) was resolved by reading `moonray/lib/rendering/rt/GeometryManager.cc`
at the pin in `UPSTREAM_LOCK.json`: `GeometryManager::finalizeChange()`'s
full-build path collects primitives to tessellate/BVH-build **exclusively**
by walking `GeometrySet` membership (`collectPrimitives()`, `:819-861`) —
`Layer` assignment is a filter applied *inside* that walk, not an alternate
way to reach a geometry. A `Geometry` assigned in the `Layer` but never added
to a `GeometrySet` silently never renders, with no error. Every mesh
`SceneBuilder.cpp` creates is therefore added to both. See
`docs/bridge/SCENE_TRANSLATION.md` "Mesh geometry" for the full citation.

## Evidence
- `docs/evidence/phase06/` — `bridge/tests/run_phase06_tests.py` (23/23
  checks: structured `CREATE_SCENE`/`UPDATE_OBJECT`/`UPDATE_CAMERA` against
  the real bridge + MoonRay, create+render, update+re-render, delete-before-
  first-render, and an unsupported-light-class rejection), plus a real
  Blender `--background` render through the actual add-on/`RenderEngine`
  path (`background-mode-multi-object-render.png`, two mesh objects + a
  tilted `SUN` light, MoonRay-shaded).
- `docs/evidence/phase06/light-orientation-fix/` — the root-cause
  investigation this same pre-flight/implementation work surfaced (see
  SCENE_TRANSLATION.md "Lights"), unrelated to the protocol shape itself but
  found while building the fixture scenes used to validate it.

## Consequences
### Positive
- `UPDATE_OBJECT`/`UPDATE_CAMERA` are no longer "recognized but
  `NOT_IMPLEMENTED`" placeholders — real, tested message handlers.
- Update/delete-before-render semantics are proven at the wire level, ahead
  of Phase 08 needing them for the viewport.
- No ASCII round-trip: mesh/camera/light attributes are typed at the RDL2 API
  boundary (`AttributeKey`-equivalent `set<T>(name, value)` calls), removing
  a whole class of text-formatting bugs the `.rdla`-writer approach carried
  (float `repr()` precision, manual quoting/escaping).

### Costs / open follow-ups
- Mid-session delete **after** a render has already happened in the same
  live `RenderContext` is not proven to remove geometry from a subsequent
  render (`RenderContext::startFrame()`'s `mSceneUpdated` path uses
  `rt::ChangeFlag::UPDATE`, which is additive/refresh-oriented, not proven to
  shrink an already-built BVH). Not a Phase 06 blocker (the add-on launches
  one fresh bridge process per render); a real open item for Phase 08.
- `UPDATE_OBJECT`'s `attrs` map (light class-specific attributes) is
  Float-only by construction — sufficient for Phase 06's confirmed attribute
  set (radius, angles, width/height, spread) but would need a typed-value
  wrapper if a non-Float class-specific attribute (e.g. an Int enum like
  `sidedness`) needs exposing later.
- Full `SceneObject` destruction (`SceneContext::deleteSceneObject()`) is not
  implemented — `delete` only removes `GeometrySet`/`LightSet` membership,
  since proving safe `Layer` un-assignment first would need an API this pin's
  `Layer.h` does not expose (`assign()` only, no `unassign()`). Acceptable
  for Phase 06 (the geometry correctly stops rendering); revisit if actual
  memory reclamation across a long-lived session becomes a real Phase 08/11
  concern.

## Revisit triggers
- Phase 08 viewport work needs mid-session delete-after-render to actually
  work — investigate `ChangeFlag::ALL` forcing or another `RenderContext`
  mechanism at that point, per the open item above.
- A light class needs a non-Float class-specific attribute exposed through
  `UPDATE_OBJECT`'s `attrs` map.
- Phase 11 packaging/stability work finds `GeometrySet`-membership-only
  delete insufficient (e.g. a real memory-growth problem across a long
  session) and needs full `SceneObject` destruction after all.
