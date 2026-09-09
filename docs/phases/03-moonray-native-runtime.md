# Phase 03 — Reproducible native MoonRay runtime

Status: CURRENT — PRE-BUILD AUDIT COMPLETE — BUILD BLOCKED ON USER APPROVAL

## Goal
Build or install a pinned standalone MoonRay runtime inside the validated Linux/WSL environment, independent of Hydra, and prove a minimal CPU render from MoonRay-native tooling/APIs.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Pin exact MoonRay source/release and native dependencies.
- Build/install MoonRay and scene_rdl2 reproducibly.
- Prove CPU renderer startup and a minimal known scene/render.
- Document runtime environment, DSOs, logs and rollback.

## Out of scope
- hdMoonray/Hydra integration.
- Blender add-on/RenderEngine integration.
- Viewport.
- XPU acceptance.

## Tasks
- [x] Verify current upstream build prerequisites from primary sources — `docs/research/03-upstream-pin-audit.md`.
- [x] Record exact source commits/tags/checksums, reconciled against the openmoonray superproject gitlinks — `UPSTREAM_LOCK.json`, `configs/moonray-source-lock.json`.
- [ ] Create reproducible build/install script (plan prepared, not executed — `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md`).
- [ ] Run minimal MoonRay CPU render.
- [ ] Capture logs/output/checksums.

## Acceptance criteria
- [ ] Fresh shell can reproduce MoonRay runtime from documented steps.
- [ ] Standalone CPU render succeeds with observed output.
- [ ] scene_rdl2/MoonRay library/runtime paths are known.
- [ ] No Hydra dependency is required for baseline render.

## Verification
- Build logs and version commands.
- Minimal render artifact.
- Clean-environment rerun or reproducibility check.

## Pre-build audit (complete, 2026-09-09)
The exact upstream source revisions intended for this phase's build were reconciled against
the `OpenMoonRay/openmoonray` superproject's own submodule gitlinks (not independently
fetched "latest" branch tips) and against the official Blender GitHub mirror. No mismatches
were found; two build-critical repositories (`mcrt_denoise`, `cmake_modules`) were identified
and added to the lock. Full detail: `docs/research/03-upstream-pin-audit.md`. A build plan was
prepared and is ready for execution: `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md`. Nothing
was built, installed, or rendered by this audit.

## Completion Record
Status: NOT STARTED — pre-build audit complete, build not yet attempted.

When complete, write `docs/completions/03-moonray-native-runtime.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
