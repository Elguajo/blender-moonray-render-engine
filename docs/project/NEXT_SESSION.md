# Next Session — Direct MoonRay Render Engine for Blender 5.2+

## Current state
Phases 00–04 are complete. No phase is currently `[>]`. **Phase 05 (Blender
RenderEngine integration and first F12 frame,
`docs/phases/05-blender-renderengine-integration.md`) requires explicit user
approval before it may begin.**

The verified foundation physically exists on the workstation `DESKTOP-9O2U790`:

```text
Windows 11 build 10.0.26100.9445
└── WSL 2.6.3.0 + WSLg 1.0.71, kernel 6.6.87.2
    └── Rocky Linux 9.8 — distro "MoonRay-Rocky9"
        ├── Blender 5.2.1 LTS Linux, GUI verified through WSLg
        ├── MoonRay CPU runtime, built from pinned source, render-verified
        └── moonray_bridge prototype, built + smoke-tested (14/14 checks)
```

## Phase 04 outcome (2026-09-10) — read before touching `bridge/`
A minimal native `moonray_bridge` process exists at `bridge/` (source) and was
proven, over a real Unix-domain-socket connection with a real test client
(`bridge/client/bridge_client.py`), to: complete a versioned `HELLO` handshake
and reject a mismatched version before any scene exchange; load a known-good
`.rdla` scene through the direct MoonRay `RenderContext` API; run one
synchronous batch render; publish the beauty buffer via POSIX shared memory
(read directly by the client, not via a re-opened export file); reject
malformed/unsupported input with structured `ERROR` responses without
corrupting the connection; and survive a hard `SIGKILL` with the client
observing a clean failure and a fresh bridge process handling a new session
normally. Full detail: `docs/completions/04-direct-bridge-prototype.md`,
`docs/evidence/phase04/`, `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md`.

**Not yet implemented by the prototype** (explicitly out of Phase 04 scope,
owned by later phases): canonical Blender→RDL2 scene/mesh/material
translation (`CREATE_SCENE` only loads a full `.rdla` file path — Phase 06/07),
progressive/animation render modes (`START_RENDER` only supports
`render_mode: "final"` — Phase 08/09), `STOP_RENDER`/`UPDATE_OBJECT`/
`UPDATE_CAMERA`/`UPDATE_MATERIAL` (recognized message types, return
`ERROR` category 2 `NOT_IMPLEMENTED_PHASE04`), and any Blender-side code at
all (no add-on exists yet — that is Phase 05).

### A real bug was found and fixed here — load-bearing lesson for later phases
`moonray::rndr::RenderContext` stores its `RenderOptions` constructor argument
**by reference**, not by value (`RenderOptions& mOptions;` member). Any code
that constructs a `RenderContext` must keep its `RenderOptions` alive for at
least as long as that `RenderContext`, and — matching the reference CLI
(`moonray/cmd/raas_cmd/moonray/moonray.cc`) — should use the **same**
`RenderOptions` instance for both `moonray::rndr::initGlobalDriver()` and
every `RenderContext` it constructs. Getting this wrong produced a
perfectly reproducible crash whose symptom (the arena allocator reporting
allocation requests in the hundreds-of-GB to multi-TB range) looked
unrelated to the real cause. Full root-cause writeup, including a secondary
diagnostic-tooling pitfall (an overly tight `ulimit -v` safety cap producing
an unrelated thread-creation failure) that had to be distinguished from the
real bug: `docs/evidence/phase04/README.md`. `bridge/src/RenderSession.h`
carries the same warning as a code comment. This class of bug (a native
object outliving what it's supposed to reference) is worth watching for again
whenever Phase 06+ adds more MoonRay API objects to the bridge.

### Bridge build/run facts carried forward
- Build: `scripts/linux/phase04_build_bridge.sh` (source read from `/mnt/d/...`,
  build directory `/root/moonray-blender/build/bridge04`, Linux-native per the
  "never build under `/mnt/*`" rule). `CMAKE_PREFIX_PATH` **must** be an
  exported environment variable, not a `-D` cache flag — CMake only splits the
  environment-variable form on `:`; a cache variable needs `;` instead. The
  same `*_ROOT`/`CMAKE_MODULES_ROOT`/`ISPC` hint variables
  `phase03_build_moonray.sh` exports are also required for
  `SceneRdl2Config.cmake`'s own `find_dependency()` calls to resolve.
- Runtime env vars the bridge needs (same as Phase 03's `moonray` CLI):
  `RDL2_DSO_PATH=/root/moonray-blender/install/openmoonray/rdl2dso`,
  `REZ_MOONRAY_ROOT=/root/moonray-blender/install/openmoonray`.
- Cold-start timing varies a lot with OS page-cache state: a bridge's first
  launch after a fresh build took ~16s to reach "listening"
  (`initGlobalDriver()`'s thread-pool/global-state init); a warm relaunch
  took ~1.2s. Don't set a tight startup timeout in any future launcher code.
- JsonCpp (control-plane wire encoding) is already a transitive dependency of
  the pinned Phase 03 SceneRdl2 build (`SceneRdl2Config.cmake`'s own
  `find_dependency(JsonCpp)`) — no new third-party dependency was added.
- `-march=core-avx2 -mavx` is still mandatory for any translation unit
  including MoonRay headers (carried forward from the Phase 04 kickoff brief,
  reconfirmed by this phase's own build).
- Test/reproduce: `python3 -u bridge/tests/run_phase04_tests.py` inside the
  distro. **Tooling note for whoever drives this next**: passing multi-line
  bash through `wsl.exe -d MoonRay-Rocky9 -- bash -lc '...'` as an inline
  argument was unreliable this session for this particular long-running,
  subprocess-spawning script (repeatedly returned instantly with exit code 9
  and zero output, for reasons never conclusively identified — not a WSL
  crash, confirmed by an immediate follow-up trivial command succeeding).
  Writing the script to a file and running
  `wsl.exe -d MoonRay-Rocky9 -- bash -s < script.sh` was reliable throughout
  this entire phase and is the pattern to prefer for anything beyond a single
  short command.

## Durable decisions
- Windows 11 workstation host; Blender + MoonRay-facing runtime execute under WSL2/WSLg Linux.
- Blender baseline: 5.2.1 LTS until an explicit compatibility migration.
- Direct Blender `RenderEngine` ↔ MoonRay bridge is primary (ADR-0002).
- MoonRay runs in a separate native Bridge Process for crash/dependency isolation
  (ADR-0002, corroborated by ADR-0003's survey of V-Ray/Octane for Blender).
- Bridge IPC: Unix domain socket, JSON envelope (JsonCpp) with 4-byte
  length-prefixed framing; bulk framebuffer data via POSIX shared memory,
  interleaved RGBA float32 (ADR-0004).
- Hydra/hdMoonray is reference/fallback/benchmark only; never silently restore it as primary.
- CPU is the mandatory first render baseline. XPU/CUDA is a separate evidence gate.
- Do not claim Direct Bridge is faster than Hydra until Phase 10 benchmark evidence exists.
- No non-local network listener by default (satisfied structurally: the bridge has no
  `AF_INET` code path at all, not just a disabled-by-default flag).

## Key facts carried forward from Phase 03
- Installed runtime: `/root/moonray-blender/install/openmoonray` — `bin/` (incl. `moonray`,
  `rdl2_json_exporter`, `denoise`), `lib64/`, `include/`, `rdl2dso/` (348 DSOs), `coredata/`.
- Third-party dependency build: `/opt/MoonRay/installs` (Linux-native ext4, upstream's own
  hardcoded default).
- Pinned source: `/root/moonray-blender/src/openmoonray` at superproject
  `b9b0ac29135b26e20a51edf9028558bb64df6700`; only `cmake_modules`, `scene_rdl2`,
  `mcrt_denoise`, `moonray`, `moonshine` are initialized. Hydra/Arras/USD/rats/moonray_gui
  submodules are deliberately uninitialized. Do not initialize them.
- Built CPU-only: `MOONRAY_USE_OPTIX=NO` in all four `CMakeCache.txt`. GPU/XPU is **not**
  proven on this machine and must not be claimed.
- Known-good test scene: `/root/moonray-blender/src/openmoonray/testdata/rectangle.rdla`
  (512×512, `DwaBaseMaterial`, `EnvLight`) — used by both Phase 03's CLI render check and
  Phase 04's bridge smoke test.

## Verified host facts (Phase 02/03, observed)
- Distro: `MoonRay-Rocky9`, Rocky Linux 9.8, WSL2, root user, systemd active.
- Distro VHDX: `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9`.
- Linux-native runtime root: `/root/moonray-blender` on ext4 `/dev/sdd` (~945 GB free).
- Blender: 5.2.1 LTS, hash `9e2066aef7ef`, at `/root/moonray-blender/tools/blender-current/blender`;
  launcher `~/bin/blender-moonray-host` (forces X11). Bundled Python 3.13.13.
- Hardware: Xeon E5-2690 v4 (28 threads), 31.8 GiB host RAM (15 GiB visible to WSL), RTX 3060 12 GB.
- Toolchain: gcc/g++ 11.5.0, cmake 3.31.8, ninja 1.10.2, system python3 3.9.25, git 2.52.0.
  `gdb` 16.3 was installed this session (`dnf install gdb`) for Phase 04 crash diagnosis and
  remains available.
- **Known limitation:** WSLg OpenGL is software (`llvmpipe`) — Rocky's Mesa has no `d3d12`
  Gallium driver. Non-blocking for CPU rendering; a real input to Phase 08.

## Practical notes
- Enter the distro with `wsl -d MoonRay-Rocky9`; the repo is visible at
  `/mnt/d/01_DEV/blender-moonray-render-engine`.
- Keep all build trees under `/root/moonray-blender`, never on `/mnt/*`.
- From Git Bash, prefix `wsl.exe` calls with `MSYS_NO_PATHCONV=1`.
- **Prefer piping scripts via stdin over inline `bash -lc '...'` arguments** —
  short variables can get mangled through the interop, and (per this
  session's Phase 04 experience) longer/subprocess-spawning inline commands
  were flaky for unclear reasons. Write to a temp file and run
  `wsl.exe -d MoonRay-Rocky9 -- bash -s < script.sh`.
- Calling `wsl.exe` from PowerShell 5.1 needs `$env:WSL_UTF8=1` and tolerance for native
  stderr; see `Invoke-Wsl` in `scripts/windows/phase02_setup_wsl_rocky.ps1`.
- Do not overwrite `/root/moonray-blender/logs/phase03-rectangle.exr` or
  `logs/phase03-build/*.log` — Phase 03 evidence with recorded checksums.
- WSL sees 15 GiB RAM; `-j 8` was sufficient for every build so far.
- A crash class exists (see "A real bug was found and fixed" above) that, at least once,
  appeared to destabilize the WSL2 VM itself (kernel fault register dump + a subsequent
  fresh boot sequence in `dmesg`), not just the one process. If a future session hits a
  similarly reproducible crash with implausibly large allocation requests, suspect a native
  lifetime bug before assuming it's environmental, and consider a generous `ulimit -v`
  (tens of GB, not single-digit — an 8 GB cap was itself observed to cause an unrelated
  thread-creation failure under MoonRay's normal 28-thread startup) as a safety net while
  diagnosing.

## Supporting repository infrastructure
- `UPSTREAM_LOCK.json` — canonical pinned upstream commits; do not choose new commits ad hoc.
- `configs/moonray-source-lock.json` — machine-readable CPU-baseline build manifest.
- `docs/research/03-upstream-pin-audit.md` — pin reconciliation and submodule classification.
- `docs/research/04-prior-blender-moonray-implementations.md` — survey of prior public
  MoonRay-for-Blender attempts.
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — original Phase 03 plan plus a correction note.
- `scripts/linux/phase03_*.sh`, `scripts/linux/phase04_build_bridge.sh` — the executed,
  reproducible build scripts for each phase so far.
- `docs/vendor/openmoonray/developer-reference/` — pinned local mirror of upstream docs.
  Search it for API topics rather than loading the tree into context.
- `docs/bridge/*.md` — the bridge protocol contract; Phase 04's "Decided vs. open" rows are
  now closed out (wire format, IPC mechanism, bulk-data reference format, pixel layout, first
  `ERROR.code` values). Scene-translation field layout, incremental-update wire semantics,
  viewport cadence and restart policy remain explicitly Open for Phase 06/07/08/11.

## Read first
1. `AGENTS.md` / `CLAUDE.md`
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md` (this file)
6. `docs/completions/04-direct-bridge-prototype.md` + `docs/evidence/phase04/` for what Phase 04
   actually proved
7. `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md` and
   `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md`
8. `docs/phases/05-blender-renderengine-integration.md` before Phase 05 is approved to start

## Mandatory phase protocol
1. Execute only the current approved phase.
2. Verify acceptance criteria with observed evidence.
3. Update the phase Completion Record.
4. Write/update `docs/completions/NN-<slug>.md` and `docs/evidence/phaseNN/`.
5. Update Architecture/ADR only for material decisions.
6. Mark the current phase `[x]` in Roadmap and activate the next phase only per the user's instruction.
7. Overwrite NEXT_SESSION with exact resume state.
8. Stop and ask in Russian: `Phase NN завершён. Переходим к Phase NN+1?`
9. Only after explicit approval execute the next phase.

## Planned sequence after Phase 04
- 05: Blender `RenderEngine`, first F12 MoonRay frame, launching/version-checking
  `moonray_bridge` from the add-on over the protocol Phase 04 implemented.
- 06: geometry/transforms/camera/lights translation (canonical bridge scene schema,
  replacing Phase 04's raw `.rdla`-path `CREATE_SCENE`).
- 07: materials/textures/instances.
- 08: progressive Rendered Viewport (watch the software-GL limitation).
- 09: final/AOV/animation/EXR.
- 10: incremental updates + direct-vs-Hydra benchmark if Hydra comparison is available.
- 11: recovery/packaging/installer.
- 12: production acceptance/release.

## Reporting
Report observed facts only: Result, Manual check, Files changed, Validation, Important
decisions, Remaining risks. Never claim a renderer/build/test works unless actually observed.
