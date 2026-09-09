# AGENT HANDOFF — MoonRay Blender Bridge

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

Current phase is Phase 02 until real Windows/WSL/Blender evidence passes.
