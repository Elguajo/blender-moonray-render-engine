# Next Session — Direct MoonRay Render Engine for Blender 5.2+

## Current state
Phase 00 and Phase 01 are complete. The user approved a material architecture change: **Direct MoonRay Bridge is now the primary integration path**. ADR-0002 records this decision. Phase 02 remains the current approved phase because WSL2/Blender host validation is still required regardless of integration path.

## Durable decisions
- Windows 11 workstation host.
- Blender + MoonRay-facing runtime execute under WSL2/WSLg Linux.
- Blender baseline: 5.2.1 LTS until an explicit compatibility migration.
- Direct Blender `RenderEngine` ↔ MoonRay bridge is primary.
- MoonRay initially runs in a separate native Bridge Process for crash/dependency isolation.
- IPC/shared-memory/binary transport is expected; exact protocol is a Phase 04 decision.
- Hydra/hdMoonray is reference/fallback/benchmark only; do not silently restore it as the primary architecture.
- CPU is mandatory first render baseline. XPU/CUDA is separate evidence gate.
- Do not claim Direct Bridge is faster than Hydra until Phase 10 benchmark evidence exists.

## Read first
1. `AGENTS.md` / `CLAUDE.md` as applicable.
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md`
6. `docs/phases/02-host-runtime-foundation.md`
7. `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md`
8. Phase 01 completion only if historical context is needed.

## Current assignment — Phase 02 only
Execute and verify the real workstation host foundation:
- WSL2/WSLg identity/version;
- Rocky Linux baseline;
- Blender 5.2.1 Linux GUI through WSLg;
- Linux-native source/build/install/runtime paths;
- Blender Python/runtime identity and `.blend` save/reopen smoke test;
- GPU visibility as non-blocking evidence (not proof of MoonRay XPU support).

Do not build MoonRay/Bridge until Phase 02 is PASS.

## Mandatory phase protocol
1. Execute only the current approved phase.
2. Verify acceptance criteria with observed evidence.
3. Update the phase Completion Record.
4. Write/update `docs/completions/NN-<slug>.md`.
5. Update Architecture/ADR only for material decisions.
6. Mark current phase `[x]` in Roadmap, but do not activate next phase without user approval.
7. Overwrite NEXT_SESSION with exact resume state.
8. Stop and ask in Russian: `Phase NN завершён. Переходим к Phase NN+1?`
9. Only after explicit approval set next phase `[>]` and execute it.

## Planned sequence after Phase 02
- 03: native MoonRay runtime, no hdMoonray requirement.
- 04: smallest native bridge + renderer proof + IPC contract.
- 05: Blender `RenderEngine`, first F12 MoonRay frame.
- 06: geometry/transforms/camera/lights.
- 07: materials/textures/instances.
- 08: progressive Rendered Viewport.
- 09: final/AOV/animation/EXR.
- 10: incremental updates + direct-vs-Hydra benchmark if Hydra comparison is available.
- 11: recovery/packaging/installer.
- 12: production acceptance/release.

## Reporting
Report observed facts only: Result, Manual check, Files changed, Validation, Important decisions, Remaining risks. Never claim a renderer/build/test works unless actually observed.
