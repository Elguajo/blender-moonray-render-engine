# Claude Code Entry Point

Read and obey `AGENT_HANDOFF.md`, then use the canonical project state under `docs/project/` (or `.progressive/project/` if Progressive Runtime has been installed).

Important architecture constraint: **Direct MoonRay Bridge is primary. Hydra/hdMoonray is reference/fallback/benchmark only.** Do not revert this without new evidence + explicit user decision/ADR.

Execute only the single current `[>]` phase and stop after phase completion for user approval.
