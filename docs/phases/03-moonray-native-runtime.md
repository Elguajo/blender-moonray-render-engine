# Phase 03 — Reproducible native MoonRay runtime

Status: COMPLETE — 2026-09-09. See `docs/completions/03-moonray-native-runtime.md` and `docs/evidence/phase03/`.

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
- [x] Create reproducible build/install scripts — `scripts/linux/phase03_install_packages.sh`, `scripts/linux/phase03_build_deps.sh`, `scripts/linux/phase03_build_moonray.sh`, `scripts/linux/phase03_render_test.sh` (superseding the monolithic-preset approach in `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — see that file's correction note and `docs/evidence/phase03/README.md` for why).
- [x] Run minimal MoonRay CPU render — `testdata/rectangle.rdla`, exit code 0, valid 512x512 RGBA EXR, non-constant pixel content verified.
- [x] Capture logs/output/checksums — `docs/evidence/phase03/`.

## Acceptance criteria
- [x] Fresh shell can reproduce MoonRay runtime from documented steps — verified twice via independent `wsl.exe` invocations of `scripts/linux/phase03_render_test.sh`, identical pixel statistics both times. A full clean rebuild (not just a fresh shell) was also performed and is the authoritative evidence — see `docs/evidence/phase03/README.md`.
- [x] Standalone CPU render succeeds with observed output — `docs/evidence/phase03/render-check.txt`.
- [x] scene_rdl2/MoonRay library/runtime paths are known — `docs/evidence/phase03/runtime-check.txt` (full `ldd` resolution, zero unresolved libraries).
- [x] No Hydra dependency is required for baseline render — `hydra`/`hdMoonray`/`moonshine_usd` submodules were never initialized or built; confirmed by inspecting the actual `CMakeLists.txt` dependency graph, not assumed.

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
Status: COMPLETE. See `docs/completions/03-moonray-native-runtime.md`.
