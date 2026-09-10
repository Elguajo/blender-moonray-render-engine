# AGENT HANDOFF — Direct MoonRay Render Engine for Blender 5.2+

This repository uses a phase-gated Progressive Context workflow and can be continued with Codex or Claude Code.

## Product goal
Build a production-oriented **direct MoonRay Render Engine for Blender 5.2+** on a Windows workstation via WSL2/WSLg.

Primary architecture:
```text
Blender bpy.types.RenderEngine
        ↕ local IPC / efficient bulk transport
moonray_bridge native process
        ↓
MoonRay RenderContext / scene_rdl2
```

Hydra/hdMoonray is **reference/fallback/benchmark only** after ADR-0002.

## Start sequence
Read:
1. `AGENTS.md` or `CLAUDE.md`
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md`
6. the single `[>]` phase
7. ADR-0002 when integration architecture matters

## Mandatory behavior
- Execute only the current approved phase.
- Verify current/version-sensitive facts with official primary sources.
- Never claim build/render/test/performance success unless observed.
- Never silently restore Hydra-first architecture.
- Never claim Direct Bridge is faster than Hydra without benchmark evidence.
- Preserve unrelated user changes.

## End-of-phase protocol
1. satisfy acceptance criteria with evidence;
2. write Completion Record and `docs/completions/...`;
3. update Architecture/ADR only if needed;
4. mark phase `[x]`;
5. update NEXT_SESSION;
6. STOP;
7. ask user in Russian if the next phase should begin.

Phase 02 passed on real hardware (2026-09-09): WSL2 + Rocky Linux 9.8 + Blender 5.2.1 LTS GUI verified
through WSLg. See `docs/completions/02-host-runtime-foundation.md` and `docs/evidence/phase02-host-evidence.md`.

Phase 03 (native MoonRay runtime) is COMPLETE (2026-09-09): a pinned CPU-only MoonRay runtime was
built and a standalone CPU render was verified. See `docs/completions/03-moonray-native-runtime.md`
and `docs/evidence/phase03/`. Its evidence was independently re-audited on 2026-09-10; four
documentation/tooling defects were corrected (commit `6a75ccd`), no build or render result changed.

Phase 04 (Direct MoonRay Bridge prototype and IPC contract) is COMPLETE (2026-09-10): a
minimal native `moonray_bridge` process was built and proven to render a known scene
through the direct MoonRay API, deliver the framebuffer via POSIX shared memory, reject a
version mismatch and malformed input cleanly, and survive a hard crash/restart without
corrupting the client. See `docs/completions/04-direct-bridge-prototype.md`,
`docs/evidence/phase04/` and `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md`.

Phase 05 (Blender RenderEngine integration and first F12 frame) is COMPLETE (2026-09-10): the
`addon/` package registers MoonRay as a Blender Render Engine, launches/version-checks the
Phase 04 bridge, translates a minimal baseline scene, and renders it via a real `F12` keypress
in the actual Blender GUI (WSLg), verified by screenshot. A real MoonRay-side lighting anomaly
(SphereLight and non-axis-aligned DistantLight both fail to illuminate module-authored geometry
in this build) was found, investigated, and worked around with an axis-snapped DistantLight
approximation — not root-caused, flagged for later phases. See
`docs/completions/05-blender-renderengine-integration.md` and `docs/evidence/phase05/`.
No phase is currently `[>]`. Phase 06 requires explicit user approval before it may begin.
