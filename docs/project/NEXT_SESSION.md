# Next Session — Direct MoonRay Render Engine for Blender 5.2+

## Current state
Phases 00–05 are complete. No phase is currently `[>]`. **Phase 06
(Geometry, transforms, camera and lights translation,
`docs/phases/06-geometry-camera-lights.md`) requires explicit user
approval before it may begin.**

The verified foundation physically exists on the workstation `DESKTOP-9O2U790`:

```text
Windows 11 build 10.0.26100.9445
└── WSL 2.6.3.0 + WSLg 1.0.71, kernel 6.6.87.2
    └── Rocky Linux 9.8 — distro "MoonRay-Rocky9"
        ├── Blender 5.2.1 LTS Linux, GUI verified through WSLg
        ├── MoonRay CPU runtime, built from pinned source, render-verified
        ├── moonray_bridge prototype, built + smoke-tested (14/14 checks)
        └── addon/ MoonRay Blender add-on, F12 render-verified through the real GUI
```

## Phase 05 outcome (2026-09-10) — read before touching `addon/`
A Blender add-on (`addon/`) registers `MoonRay` as a selectable Render
Engine, launches/version-checks a fresh `moonray_bridge` process per render,
translates Blender's baseline scene (exactly one camera + one mesh + one
point light — anything else is a clean, reported `SceneTranslationError`,
not a crash) into a self-contained `.rdla` file, drives `CREATE_SCENE` +
`START_RENDER("final")`, and copies the resulting framebuffer directly into
`RenderResult`. Verified via a real `F12` keypress in the actual Blender GUI
(WSLg), screenshot evidence in `docs/evidence/phase05/f12-gui-render.png`.
Full detail: `docs/completions/05-blender-renderengine-integration.md`,
`docs/evidence/phase05/`.

### A real MoonRay-side anomaly was found — load-bearing, read before adding light types
`SphereLight` (the natural translation of Blender's default point light)
reproducibly fails to illuminate `RdlMeshGeometry` authored by this
project's own vertex-authoring code in this pinned MoonRay build —
camera-visible faces render flat black — while the same geometry shades
correctly under `EnvLight` or an axis-aligned `DistantLight`. A second,
independent anomaly: even `DistantLight` fails the same way for a
mathematically verified, correctly-oriented, orthonormal but
*non-axis-aligned* `node_xform`. Neither was root-caused (out of Phase 05's
"minimal translation" scope); both are worked around in
`addon/scene_writer.py` by approximating the point light as a `DistantLight`
whose direction is snapped to the nearest world axis. Full investigation
with 10 numbered diagnostic tests: `docs/evidence/phase05/sphere-light-investigation/README.md`.
**Before adding any new light type in Phase 06/07, re-read that file** — the
same anomaly will very likely resurface for `RectLight`/`SpotLight`/etc. and
for general (non-axis-aligned) light orientations, and will need either a
similar workaround, a root-cause fix, or an upstream MoonRay report.

### Bridge protocol was not changed
Phase 05 is a pure consumer of the unmodified Phase 04 `moonray_bridge`
binary and wire protocol — `CREATE_SCENE` still only accepts an `.rdla` file
path (no canonical scene-object schema yet). `docs/bridge/MESSAGE_SCHEMA.md`'s
"Open — Phase 04/06/07" per-message payload field layout is unchanged;
Phase 06 is expected to be the phase that actually needs to extend it (or
formally decide not to and keep writing `.rdla` files from Python) once
general, incremental scene translation is in scope. That is a material
protocol decision if made — document it in `docs/bridge/*.md` and/or a new
ADR when Phase 06 gets there, per `docs/bridge/PROTOCOL.md`'s own "Decided
vs. open" convention.

### Bugs found and fixed in `addon/` during Phase 05 evidence-gathering
1. `addon/bridge_client.py`'s socket kept its 5s `connect_timeout` as the
   ongoing timeout for *all* subsequent reads (a `socket.settimeout()`
   footgun — it doesn't only apply to the call it preceded). A real,
   in-progress, successful render longer than 5s (routine at higher
   resolution/sample counts) was misreported as a bridge crash. Fixed by
   clearing the timeout (`settimeout(None)`) right after `connect()`
   succeeds. **If you add a new bridge client anywhere else, replicate this
   fix** — the same footgun will reappear with any `socket.settimeout()`
   call whose scope isn't deliberately re-considered after the connect.
2. `RenderPass.rect` needs a sequence of `(w*h)` per-pixel `(channels,)`
   float-tuples, not one flat `w*h*channels`-length list. See
   `addon/engine.py::_write_result` for the correct shape.

### GUI automation environment notes (useful for future phases needing GUI evidence)
- `bpy.ops.render.render('INVOKE_DEFAULT')` called from a `bpy.app.timers`
  callback silently no-ops (no window/area context) — use the operator's
  default execution context (`bpy.ops.render.render(write_still=False)`)
  from a timer instead if scripting a render trigger.
- Windows-side synthetic mouse/keyboard input (this session's desktop
  automation) is unreliable against the WSLg-forwarded Blender window
  (clicks landing off-target, key presses not arriving at all). `xdotool`
  (installed into `MoonRay-Rocky9` via `dnf install xdotool` — now part of
  the distro's installed packages, not scripted/pinned anywhere) sending
  `key --window <id> F12` directly to the X11 window was reliable. Find the
  window id with `DISPLAY=:0 xdotool search --name Blender`.
- Pass multi-command scripts to `xdotool`/bash via a file + stdin
  (`wsl.exe ... -- bash -s < script.sh`), same reasoning as the existing WSL
  practice note below — inline `bash -c "...$VAR..."` through nested
  Windows/WSL quoting mangled variable expansion during this phase's own
  evidence-gathering too.

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
- Phase 05's `moonray_bridge` process lifecycle is one-shot per render (launch, use, tear
  down), not a persistent long-lived process across renders — revisit only with a real
  measured need (e.g. cold-start cost becoming a Phase 08 viewport-latency problem).
- Blender's point lights are approximated as axis-snapped `DistantLight`s pending either a
  root-cause fix for the SphereLight/DistantLight anomaly above or a deliberate, evidenced
  decision to keep the approximation into Phase 06/07.

## Key facts carried forward from Phase 03
- Installed runtime: `/root/moonray-blender/install/openmoonray` — `bin/` (incl. `moonray`,
  `rdl2_json_exporter`, `denoise`, `rdl2_print`, `rdl2_convert`), `lib64/`, `include/`,
  `rdl2dso/` (348 DSOs), `coredata/`.
- Third-party dependency build: `/opt/MoonRay/installs` (Linux-native ext4, upstream's own
  hardcoded default).
- Pinned source: `/root/moonray-blender/src/openmoonray` at superproject
  `b9b0ac29135b26e20a51edf9028558bb64df6700`; only `cmake_modules`, `scene_rdl2`,
  `mcrt_denoise`, `moonray`, `moonshine` are initialized. Hydra/Arras/USD/rats/moonray_gui
  submodules are deliberately uninitialized. Do not initialize them.
- Built CPU-only: `MOONRAY_USE_OPTIX=NO` in all four `CMakeCache.txt`. GPU/XPU is **not**
  proven on this machine and must not be claimed.
- Known-good test scene: `/root/moonray-blender/src/openmoonray/testdata/rectangle.rdla`
  (512×512, `DwaBaseMaterial`, `EnvLight`) — used by Phase 03/04's own tests and as a
  reference/control scene in Phase 05's SphereLight investigation.
- `rdl2_print` (installed runtime `bin/rdl2_print`) dumps SceneClass attributes/defaults/
  comments for any DSO on `RDL2_DSO_PATH` — use it to ground any new RDL2 object's exact
  attribute names before authoring `.rdla` text by hand or from Python, as Phase 05 did for
  `BoxGeometry`/`DistantLight`/`PerspectiveCamera`/`DwaBaseMaterial`/`SceneVariables`.

## Verified host facts (Phase 02/03, observed)
- Distro: `MoonRay-Rocky9`, Rocky Linux 9.8, WSL2, root user, systemd active.
- Distro VHDX: `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9`.
- Linux-native runtime root: `/root/moonray-blender` on ext4 `/dev/sdd` (~945 GB free).
- Blender: 5.2.1 LTS, hash `9e2066aef7ef`, at `/root/moonray-blender/tools/blender-current/blender`;
  launcher `~/bin/blender-moonray-host` (forces X11). Bundled Python 3.13.13.
- Hardware: Xeon E5-2690 v4 (28 threads), 31.8 GiB host RAM (15 GiB visible to WSL), RTX 3060 12 GB.
- Toolchain: gcc/g++ 11.5.0, cmake 3.31.8, ninja 1.10.2, system python3 3.9.25, git 2.52.0.
  `gdb` 16.3 (Phase 04) and `xdotool`/`libxdo`/`libXtst` (Phase 05, for GUI-evidence
  automation) are installed in the distro and remain available.
- **Known limitation:** WSLg OpenGL is software (`llvmpipe`) — Rocky's Mesa has no `d3d12`
  Gallium driver. Non-blocking for CPU rendering; a real input to Phase 08.

## Practical notes
- Enter the distro with `wsl -d MoonRay-Rocky9`; the repo is visible at
  `/mnt/d/01_DEV/blender-moonray-render-engine`.
- Keep all build trees under `/root/moonray-blender`, never on `/mnt/*`.
- From Git Bash, prefix `wsl.exe` calls with `MSYS_NO_PATHCONV=1`.
- **Prefer piping scripts via stdin over inline `bash -lc '...'` arguments** —
  short variables can get mangled through the interop, and (per this
  session's Phase 04 *and* Phase 05 experience) longer/subprocess-spawning
  or variable-heavy inline commands were flaky for unclear reasons. Write to
  a temp file and run `wsl.exe -d MoonRay-Rocky9 -- bash -s < script.sh`.
- Calling `wsl.exe` from PowerShell 5.1 needs `$env:WSL_UTF8=1` and tolerance for native
  stderr; see `Invoke-Wsl` in `scripts/windows/phase02_setup_wsl_rocky.ps1`.
- Do not overwrite `/root/moonray-blender/logs/phase03-rectangle.exr` or
  `logs/phase03-build/*.log` — Phase 03 evidence with recorded checksums.
- WSL sees 15 GiB RAM; `-j 8` was sufficient for every build so far.
- A crash class exists (Phase 04) that, at least once, appeared to destabilize the WSL2 VM
  itself (kernel fault register dump + a subsequent fresh boot sequence in `dmesg`), not just
  the one process. If a future session hits a similarly reproducible crash with implausibly
  large allocation requests, suspect a native lifetime bug before assuming it's environmental.
- The Blender GUI window, launched via WSLg, appears as a real Windows window (WSLg's own
  RDP-based integration) — a Windows-side screenshot tool can capture it directly (Phase 05
  used `System.Drawing`/`CopyFromScreen` via PowerShell for full-resolution capture). Mouse/
  keyboard automation from the Windows side was unreliable against this window; `xdotool`
  from inside the distro (`DISPLAY=:0`) was reliable — see "GUI automation environment notes"
  above.

## Supporting repository infrastructure
- `UPSTREAM_LOCK.json` — canonical pinned upstream commits; do not choose new commits ad hoc.
- `configs/moonray-source-lock.json` — machine-readable CPU-baseline build manifest.
- `docs/research/03-upstream-pin-audit.md` — pin reconciliation and submodule classification.
- `docs/research/04-prior-blender-moonray-implementations.md` — survey of prior public
  MoonRay-for-Blender attempts.
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — original Phase 03 plan plus a correction note.
- `scripts/linux/phase03_*.sh`, `scripts/linux/phase04_build_bridge.sh` — the executed,
  reproducible build scripts for each phase so far. Phase 05 added no new build script (it
  consumes the existing Phase 04 bridge binary/build unchanged).
- `docs/vendor/openmoonray/developer-reference/` — pinned local mirror of upstream docs.
  Search it for API topics rather than loading the tree into context.
- `docs/bridge/*.md` — the bridge protocol contract; unchanged by Phase 05. Scene-translation
  field layout, incremental-update wire semantics, viewport cadence and restart policy remain
  explicitly Open for Phase 06/07/08/11.
- `addon/` — the Blender add-on package (Phase 05). `bridge_client.py` here is the add-on's
  own production copy, separate from (and now ahead of, re: the timeout fix above)
  `bridge/client/bridge_client.py`, which remains the Phase 04 test-only client.

## Read first
1. `AGENTS.md` / `CLAUDE.md`
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md` (this file)
6. `docs/completions/05-blender-renderengine-integration.md` + `docs/evidence/phase05/` for
   what Phase 05 actually proved, especially the SphereLight/DistantLight anomaly writeup
7. `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md` and
   `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md`
8. `docs/phases/06-geometry-camera-lights.md` before Phase 06 is approved to start

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

## Planned sequence after Phase 05
- 06: geometry/transforms/camera/lights translation (canonical bridge scene schema,
  replacing Phase 04/05's raw `.rdla`-path `CREATE_SCENE`; revisit the SphereLight/
  DistantLight anomaly here with more room to investigate).
- 07: materials/textures/instances.
- 08: progressive Rendered Viewport (watch the software-GL limitation).
- 09: final/AOV/animation/EXR.
- 10: incremental updates + direct-vs-Hydra benchmark if Hydra comparison is available.
- 11: recovery/packaging/installer.
- 12: production acceptance/release.

## Reporting
Report observed facts only: Result, Manual check, Files changed, Validation, Important
decisions, Remaining risks. Never claim a renderer/build/test works unless actually observed.
