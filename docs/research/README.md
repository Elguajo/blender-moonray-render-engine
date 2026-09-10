# Research

Research notes record version-sensitive/architectural evidence. They are not automatically implementation truth; current phase verification owns observed runtime results.

Key notes:
- `01-compatibility-matrix.md` — historical Blender/Hydra/MoonRay compatibility research.
- `02-host-runtime-baseline.md` — WSL2/Blender host baseline research.
- `03-direct-bridge-feasibility.md` — evidence supporting the Direct Bridge architecture.
- `03-upstream-pin-audit.md` — Phase 03 pre-build upstream dependency reconciliation audit.
- `PRIOR_ART.md` / `04-prior-blender-moonray-implementations.md` / `04-prior-implementation-matrix.json` — audit of prior public MoonRay-for-Blender integration attempts.
- `05-prior-art-harvest.md` — applied harvest from those prior implementations: corrected `SceneVariables` coverage checklist, Principled-BSDF→DwaBase mapping analysis, Phase 06-08 pitfalls, and per-fragment licensing verdicts.

ADR-0002 supersedes Hydra as the primary integration route.
