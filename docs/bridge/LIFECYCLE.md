# Bridge Lifecycle

Status: **TARGET DESIGN, not an implementation claim.** See [PROTOCOL.md](PROTOCOL.md) for
status conventions. Authoritative acceptance criteria live in
`docs/phases/04-direct-bridge-prototype.md` (process lifecycle),
`docs/phases/08-interactive-viewport.md` (viewport render mode) and
`docs/phases/11-stability-packaging.md` (recovery/watchdog policy).

## Three nested lifecycles
```text
Bridge process lifecycle
  └─ Scene-session lifecycle
       └─ Render-mode lifecycle (viewport / final / animation)
```

## 1. Bridge process lifecycle (decided shape)
```text
Blender add-on launches moonray_bridge
        ↓
version handshake  (HELLO/CAPABILITIES shape decided — see MESSAGE_SCHEMA.md;
                     exact wire encoding Open — Phase 04)
        ↓
ready — awaiting scene/control messages
        ↓ ... normal operation ...
shutdown (add-on request)  ──or──  crash (detected by add-on)
```
- The Bridge Process is launched and version-checked by the Blender integration
  (`docs/project/ARCHITECTURE.md` operational assumptions) — the bridge does not
  self-register or run as a persistent background service by default.
- A crash must be detected by the add-on; the `.blend` session survives and the add-on
  offers restart/retry (ARCHITECTURE.md failure isolation; see also
  [ERROR_MODEL.md](ERROR_MODEL.md) category 4).
- Restart/recovery **policy** (auto vs. manual, backoff, state resync) is Phase 11 scope.

## 2. Scene-session lifecycle (decided shape, per `docs/project/ARCHITECTURE.md`)
```text
Blender depsgraph change
        ↓
change classification
        ↓
canonical bridge update message
        ↓
bridge validates + maps to RDL2  (see SCENE_TRANSLATION.md; see ERROR_MODEL.md #1 on failure)
        ↓
MoonRay scene update — applied only while the renderer's lifecycle permits it
        ↓
restart or continue the in-flight render, per MoonRay's own render lifecycle rules
        ↓
progressive framebuffer/AOV snapshot  (see FRAMEBUFFER_PROTOCOL.md)
        ↓
Blender viewport redraw / RenderResult update
```
The key constraint carried over from RDL2 itself: attribute writes must be bracketed by
`SceneObject::beginUpdate()`/`endUpdate()`, and not every attribute can be changed while a
render is actively consuming the scene — "MoonRay update while not rendering (where
required)" per the ARCHITECTURE.md scene lifecycle. The bridge must know, per attribute
class, whether an update requires pausing/restarting the render — **exact per-attribute
update semantics are Open — Phase 06/07**, learned as each translation category
(geometry, camera/lights, then materials/textures) is implemented.

Full-scene sync is the accepted mechanism for the first F12 milestone; incremental
scene-session updates (the diagram above) become mandatory before viewport production
acceptance (`docs/design/DIRECT_BRIDGE_TARGET.md` rule 6).

## 3. Render-mode lifecycle (Open — phased)
Three render modes share the scene-session mechanism above but differ in cadence and
completion semantics:

| Mode | Trigger | Target phase | Completion |
|---|---|---|---|
| Progressive viewport | Rendered Viewport enabled | Phase 08 | Never "completes"; keeps refining until scene changes or viewport closes |
| Final (F12) | Render invoked | Phase 05 (first frame), Phase 09 (AOVs/EXR) | Converges to sample/time target, then delivers final `RenderResult` |
| Animation | Frame stepping during final render | Phase 09 | Repeats the final-render cycle per frame with correct frame-dependent transforms |

Cancellation must be representable in all three modes without corrupting a subsequent render
(`docs/phases/09-final-render-aovs-animation.md` acceptance: "Failures/cancel do not corrupt
later renders").

## Decided vs. open summary
| Aspect | Status |
|---|---|
| Add-on launches and version-checks the bridge process | **Decided** |
| Crash isolation: bridge crash must not take Blender down | **Decided** |
| Scene updates classified → validated → mapped → applied → rendered → snapshotted | **Decided shape** (ARCHITECTURE.md) |
| RDL2 `beginUpdate()`/`endUpdate()` bracketing for attribute writes | **Decided** (RDL2 API) |
| Version handshake sequence (`HELLO`/`CAPABILITIES`, version-mismatch rejection) | **Decided (shape) — [MESSAGE_SCHEMA.md](MESSAGE_SCHEMA.md)** |
| Version handshake wire encoding | **Open — Phase 04** |
| Per-attribute "requires render pause" classification | **Open — Phase 06/07** |
| Viewport snapshot cadence / render-mode transition messages | **Open — Phase 08** |
| Auto-restart/backoff policy after crash | **Open — Phase 11** |
