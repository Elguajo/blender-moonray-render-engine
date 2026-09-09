# Claude Code Entry Point

Read and obey `AGENT_HANDOFF.md`, then use the canonical project state under `docs/project/` (or `.progressive/project/` if Progressive Runtime has been installed).

Important architecture constraint: **Direct MoonRay Bridge is primary. Hydra/hdMoonray is reference/fallback/benchmark only.** Do not revert this without new evidence + explicit user decision/ADR.

Execute only the single current `[>]` phase and stop after phase completion for user approval.

## MoonRay API/design questions
1. Inspect `docs/vendor/openmoonray/developer-reference/` first (search for the relevant file/topic — do not load the whole tree into context).
2. Then check the pinned MoonRay source headers when an exact API/ABI/behavior matters.
3. Use current official upstream sources (https://docs.openmoonray.org/, https://github.com/OpenMoonRay/openmoonray-docs) when local docs may be stale.
4. Never infer support solely from documentation.
