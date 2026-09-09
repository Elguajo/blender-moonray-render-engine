# Repository Agent Instructions

Act as a senior engineering agent. Use Russian with the user unless requested otherwise; use English for code/technical artifacts unless repository convention differs.

## Canonical context
For non-trivial work read only the minimum required, normally:
1. `docs/project/PROJECT_BRIEF.md`
2. `docs/project/ARCHITECTURE.md`
3. `docs/project/ROADMAP.md`
4. `docs/project/NEXT_SESSION.md`
5. the single `[>]` phase
6. relevant ADR/research/tests only as needed

If `.progressive/` Project Runtime is installed, follow its router/protocols and treat synchronized state there as canonical according to its instructions.

## Non-negotiable architecture
Primary production path is **Blender RenderEngine ↔ Direct local MoonRay Bridge ↔ MoonRay**. Hydra/hdMoonray is reference/fallback/benchmark only after ADR-0002. Do not change that boundary without explicit user approval and an ADR.

Do not claim Direct Bridge is faster than Hydra without measured benchmark evidence.

## Execution
- Preserve unrelated edits; inspect git status first.
- Use official/current primary docs for version-sensitive behavior.
- Do not claim tests/builds/renders pass unless observed.
- Execute only the current approved phase.
- At phase completion persist evidence, mark it complete, update NEXT_SESSION, then stop and ask the user before activating the next phase.
- Never use Python element-by-element loops for production-scale geometry/framebuffer transfer when a native/bulk path is required.
- Treat bridge input as untrusted/corruptible; local-only listener by default.

## Reporting
Result; Manual check if needed; Files changed; Validation; Important decisions; Remaining risks.
