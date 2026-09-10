# Roadmap — Direct MoonRay Render Engine for Blender 5.2+

Legend: `[ ] PLANNED` · `[>] IN PROGRESS` · `[x] COMPLETE`

- [x] Phase 00 — Scope, constraints and durable project baseline — `docs/phases/00-scope-and-baseline.md`
- [x] Phase 01 — Compatibility research and Windows/WSL host architecture — `docs/phases/01-compatibility-and-host-architecture.md`
- [x] Phase 02 — Windows/WSL/Linux GPU and Blender GUI foundation — `docs/phases/02-host-runtime-foundation.md`
- [x] Phase 03 — Reproducible native MoonRay runtime — `docs/phases/03-moonray-native-runtime.md`
- [x] Phase 04 — Direct MoonRay Bridge prototype and IPC contract — `docs/phases/04-direct-bridge-prototype.md`
- [ ] Phase 05 — Blender RenderEngine integration and first F12 frame — `docs/phases/05-blender-renderengine-integration.md`
- [ ] Phase 06 — Geometry, transforms, camera and lights translation — `docs/phases/06-geometry-camera-lights.md`
- [ ] Phase 07 — Materials, textures and instances — `docs/phases/07-materials-textures-instances.md`
- [ ] Phase 08 — Interactive Rendered Viewport — `docs/phases/08-interactive-viewport.md`
- [ ] Phase 09 — Final render, AOVs, animation and EXR — `docs/phases/09-final-render-aovs-animation.md`
- [ ] Phase 10 — Incremental updates, benchmark and performance hardening — `docs/phases/10-incremental-performance.md`
- [ ] Phase 11 — Stability, recovery, packaging and installer — `docs/phases/11-stability-packaging.md`
- [ ] Phase 12 — Production acceptance, known limitations and release archive — `docs/phases/12-final-acceptance.md`

## Architecture note
ADR-0002 changed the renderer-integration strategy after Phase 01: **Direct Bridge is primary; Hydra/hdMoonray is reference/fallback/benchmark only.** Phase 00/01 historical completion records remain valid evidence for scope and WSL2 host research but do not override ADR-0002.

## User gate
Only one phase may be `[>]`. After a phase is verified and persisted, stop and ask the user before activating the next phase.

Project complete only when all acceptance criteria are observed and every phase is `[x]`.
