# Next Session — Direct MoonRay Render Engine for Blender 5.2+

## Current state
Phases 00–03 are complete. **Phase 04 is now `[>]` ACTIVE** — Direct MoonRay Bridge
prototype and IPC contract (`docs/phases/04-direct-bridge-prototype.md`). No
implementation work has started yet.

The verified foundation physically exists on the workstation `DESKTOP-9O2U790`:

```text
Windows 11 build 10.0.26100.9445
└── WSL 2.6.3.0 + WSLg 1.0.71, kernel 6.6.87.2
    └── Rocky Linux 9.8 — distro "MoonRay-Rocky9"
        ├── Blender 5.2.1 LTS Linux, GUI verified through WSLg
        └── MoonRay CPU runtime, built from pinned source, render-verified
```

## Current assignment — Phase 04
Build the smallest crash-isolated native `moonray_bridge` process that receives a command
from a client, constructs/loads a minimal MoonRay scene, renders through the direct
MoonRay API, and returns status plus image data — without Hydra. Full scope, tasks,
acceptance criteria and negative cases: `docs/phases/04-direct-bridge-prototype.md`.

The protocol/schema/lifecycle/error-model scaffolding already exists under `docs/bridge/`
(`PROTOCOL.md`, `MESSAGE_SCHEMA.md`, `LIFECYCLE.md`, `ERROR_MODEL.md`,
`FRAMEBUFFER_PROTOCOL.md`, `SCENE_TRANSLATION.md`). Implement or deliberately refine that
design; do not reinvent it from scratch. `bridge/` currently holds only a README by design.

## Phase 04 build prerequisites — verified 2026-09-10, not assumed
A downstream CMake consumer was actually built, linked and run against the installed
runtime (probe at `/root/moonray-blender/tmp/p04-probe`, outside the repository,
disposable). It configured, compiled, linked and executed:

```text
RenderOptions constructed; threads=28
SceneContext constructed; dsoPath="."
P04_LINK_PROBE_OK
```

- CMake package configs exported and found: `Moonray-18.4.0.0`, `SceneRdl2-16.2.0.0`,
  `McrtDenoise-7.2.0.0`, `Moonshine-15.6.0.0` (under `install/openmoonray/lib64/cmake/`).
- API entry points present: `include/moonray/rendering/rndr/RenderContext.h`
  (plus `RenderOptions.h`, `RenderOutputDriver.h`, `RenderProgressEstimation.h`,
  `RenderStatistics.h`) and `include/scene_rdl2/scene/rdl2/{SceneContext,RenderOutput}.h`.
- Link targets: `Moonray::rendering_rndr`, `Moonray::rendering_geom`,
  `SceneRdl2::scene_rdl2`, and the rest of the `Moonray::` / `SceneRdl2::` namespaces.
- The probe's `ldd` resolves into `install/openmoonray/lib64` + `/opt/MoonRay/installs`
  with zero unresolved libraries.

### MUST-KNOW: MoonRay's imported CMake targets do not propagate ISA flags
Any downstream translation unit that includes MoonRay headers fails to **compile** under
this distro's GCC 11 unless AVX flags are set explicitly:

```text
avxintrin.h:1486:19: error: '__builtin_ia32_ps256_ps' was not declared in this scope
avxintrin.h:1492:20: error: '__builtin_ia32_si256_si' was not declared in this scope
```

This reads like a broken toolchain but is a missing compile flag. The bridge's
`CMakeLists.txt` **must** set:

```cmake
target_compile_options(<target> PRIVATE -march=core-avx2 -mavx)
```

MoonRay applies these to its own targets via
`cmake_modules/cmake/MoonrayDso.cmake:18-19,43-44,53-54`, but they are not exported in the
imported targets' `INTERFACE_COMPILE_OPTIONS`. Consequence to record in the runtime
requirements: the resulting bridge binary requires an **AVX2/core-avx2** CPU. The
workstation's Xeon E5-2690 v4 satisfies this.

## Key facts carried forward from Phase 03
- Installed runtime: `/root/moonray-blender/install/openmoonray` — `bin/` (incl. `moonray`,
  `rdl2_json_exporter`, `denoise`), `lib64/`, `include/`, `rdl2dso/` (348 DSOs), `coredata/`.
- Third-party dependency build: `/opt/MoonRay/installs` (Linux-native ext4, upstream's own
  hardcoded default — see the completion record for why this was kept rather than relocated).
- Pinned source: `/root/moonray-blender/src/openmoonray` at superproject
  `b9b0ac29135b26e20a51edf9028558bb64df6700`; only `cmake_modules`, `scene_rdl2`,
  `mcrt_denoise`, `moonray`, `moonshine` are initialized. Hydra/Arras/USD/rats/moonray_gui
  submodules are deliberately uninitialized. Do not initialize them.
- Built CPU-only: `MOONRAY_USE_OPTIX=NO` in all four `CMakeCache.txt`. GPU/XPU is **not**
  proven on this machine and must not be claimed.
- Per-repository builds were used, not the monolithic `cmake --preset rocky9-release`.
  Use `scripts/linux/phase03_*.sh` as the reproducible reference, not the original
  preset-based runbook text.
- A concurrent/prior build attempt left artifacts at `/root/moonray-blender/install/deps`
  and per-repo install dirs. Not ours; leave them alone.

## Durable decisions
- Windows 11 workstation host; Blender + MoonRay-facing runtime execute under WSL2/WSLg Linux.
- Blender baseline: 5.2.1 LTS until an explicit compatibility migration.
- Direct Blender `RenderEngine` ↔ MoonRay bridge is primary (ADR-0002).
- MoonRay runs in a separate native Bridge Process for crash/dependency isolation
  (ADR-0002, corroborated by ADR-0003's survey of V-Ray/Octane for Blender).
- IPC/shared-memory/binary transport is expected; the exact protocol is a Phase 04 decision.
- Hydra/hdMoonray is reference/fallback/benchmark only; never silently restore it as primary.
- CPU is the mandatory first render baseline. XPU/CUDA is a separate evidence gate.
- Do not claim Direct Bridge is faster than Hydra until Phase 10 benchmark evidence exists.
- No non-local network listener by default; justify any serialization framework by
  requirements rather than preference.

## Verified host facts (Phase 02/03, observed)
- Distro: `MoonRay-Rocky9`, Rocky Linux 9.8, WSL2, root user, systemd active.
- Distro VHDX: `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9`.
- Linux-native runtime root: `/root/moonray-blender` on ext4 `/dev/sdd` (~949 GB free).
- Blender: 5.2.1 LTS, hash `9e2066aef7ef`, at `/root/moonray-blender/tools/blender-current/blender`;
  launcher `~/bin/blender-moonray-host` (forces X11). Bundled Python 3.13.13.
- Hardware: Xeon E5-2690 v4 (28 threads), 31.8 GiB host RAM (15 GiB visible to WSL), RTX 3060 12 GB.
- Toolchain: gcc/g++ 11.5.0, cmake 3.31.8, ninja 1.10.2, system python3 3.9.25, git 2.52.0.
- **Known limitation:** WSLg OpenGL is software (`llvmpipe`) — Rocky's Mesa has no `d3d12`
  Gallium driver. Non-blocking for CPU rendering; a real input to Phase 08.

## Practical notes
- Enter the distro with `wsl -d MoonRay-Rocky9`; the repo is visible at
  `/mnt/d/01_DEV/blender-moonray-render-engine`.
- Keep all build trees under `/root/moonray-blender`, never on `/mnt/*`.
- From Git Bash, prefix `wsl.exe` calls with `MSYS_NO_PATHCONV=1`.
- **Passing a script as an argument (`bash -lc '...'`) mangles short shell variables** —
  `$S`, `$p`, `$d` silently expand to empty through the interop. Pipe the script via stdin
  instead: write it to a temp file and run
  `wsl.exe -d MoonRay-Rocky9 -- bash -s < script.sh`.
- Calling `wsl.exe` from PowerShell 5.1 needs `$env:WSL_UTF8=1` and tolerance for native
  stderr; see `Invoke-Wsl` in `scripts/windows/phase02_setup_wsl_rocky.ps1`.
- Do not overwrite `/root/moonray-blender/logs/phase03-rectangle.exr` or
  `logs/phase03-build/*.log` — Phase 03 evidence with recorded checksums.
  `scripts/linux/phase03_render_test.sh` honours `PHASE03_OUT_EXR` for safe re-runs.
- WSL sees 15 GiB RAM; `-j 8` was sufficient for the entire Phase 03 build.

## Supporting repository infrastructure
- `UPSTREAM_LOCK.json` — canonical pinned upstream commits; do not choose new commits ad hoc.
- `configs/moonray-source-lock.json` — machine-readable CPU-baseline build manifest.
- `docs/research/03-upstream-pin-audit.md` — pin reconciliation and submodule classification.
- `docs/research/04-prior-blender-moonray-implementations.md` — survey of prior public
  MoonRay-for-Blender attempts; read before designing the bridge, it records what failed.
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — original plan plus a correction note.
- `scripts/linux/phase03_*.sh` — the executed, reproducible Phase 03 build scripts.
- `docs/vendor/openmoonray/developer-reference/` — pinned local mirror of upstream docs.
  Search it for API topics rather than loading the tree into context.

## Read first
1. `AGENTS.md` / `CLAUDE.md`
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md` (this file)
6. `docs/phases/04-direct-bridge-prototype.md` — the active phase
7. `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md`
8. `docs/bridge/*.md` — the existing protocol design
9. `docs/completions/03-moonray-native-runtime.md` + `docs/evidence/phase03/` for what is
   actually proven

## Mandatory phase protocol
1. Execute only the current approved phase.
2. Verify acceptance criteria with observed evidence.
3. Update the phase Completion Record.
4. Write/update `docs/completions/NN-<slug>.md` and `docs/evidence/phaseNN/`.
5. Update Architecture/ADR only for material decisions (the IPC protocol is a likely candidate).
6. Mark the current phase `[x]` in Roadmap and activate the next phase only per the user's instruction.
7. Overwrite NEXT_SESSION with exact resume state.
8. Stop and ask in Russian: `Phase NN завершён. Переходим к Phase NN+1?`
9. Only after explicit approval execute the next phase.

## Planned sequence after Phase 04
- 05: Blender `RenderEngine`, first F12 MoonRay frame.
- 06: geometry/transforms/camera/lights.
- 07: materials/textures/instances.
- 08: progressive Rendered Viewport (watch the software-GL limitation).
- 09: final/AOV/animation/EXR.
- 10: incremental updates + direct-vs-Hydra benchmark if Hydra comparison is available.
- 11: recovery/packaging/installer.
- 12: production acceptance/release.

## Reporting
Report observed facts only: Result, Manual check, Files changed, Validation, Important
decisions, Remaining risks. Never claim a renderer/build/test works unless actually observed.
