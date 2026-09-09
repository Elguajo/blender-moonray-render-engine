# Phase 03 — Reproducible native MoonRay runtime

Status: PLANNED

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
- [ ] Verify current upstream build prerequisites from primary sources.
- [ ] Create reproducible build/install script.
- [ ] Record exact source commits/tags/checksums.
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

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/03-moonray-native-runtime.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
