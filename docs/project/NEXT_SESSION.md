# Next Session — Direct MoonRay Render Engine for Blender 5.2+

## Current state
Phases 00, 01 and 02 are complete. The verified host foundation now physically exists on the workstation `DESKTOP-9O2U790`:

```text
Windows 11 build 10.0.26100.9445
└── WSL 2.6.3.0 + WSLg 1.0.71, kernel 6.6.87.2
    └── Rocky Linux 9.8 — distro "MoonRay-Rocky9"
        └── Blender 5.2.1 LTS Linux, GUI verified through WSLg
```

Phase 03 (native MoonRay runtime) is **COMPLETE** (2026-09-09). A pinned, CPU-only MoonRay
runtime was built inside `MoonRay-Rocky9` from the audited source snapshot
(`docs/research/03-upstream-pin-audit.md`) and a standalone CPU render of
`testdata/rectangle.rdla` was verified (exit 0, valid 512x512 RGBA EXR, non-constant pixel
content, reproduced twice from fresh shells after a clean rebuild). Full detail:
`docs/completions/03-moonray-native-runtime.md` and `docs/evidence/phase03/`. No phase is
currently `[>]`. Phase 04 requires explicit user approval before it may begin.

Key facts carried forward from Phase 03:
- Installed runtime: `/root/moonray-blender/install/openmoonray` (binaries incl. `moonray`,
  `rdl2_json_exporter`, etc. under `bin/`, libs under `lib64/`).
- Third-party dependency build: `/opt/MoonRay/installs` (Linux-native ext4, upstream's own
  hardcoded default — see the completion record for why this was kept rather than relocated).
- The monolithic `cmake --preset rocky9-release` approach in the original build plan was
  **not** used — it would have hard-failed or dragged in Hydra/hdMoonray/Arras/USD. Each
  required repository (`scene_rdl2`, `mcrt_denoise`, `moonray`, `moonshine`) was built
  separately instead, per upstream's own documented alternative. Use
  `scripts/linux/phase03_build_moonray.sh` (and the other `scripts/linux/phase03_*.sh`
  scripts) as the reproducible reference, not the original preset-based plan text.
- `moonshine` is a hard requirement (not merely a Phase 07 nice-to-have) — the canonical
  upstream test scene uses `DwaBaseMaterial`, which lives in `moonshine`.
- A concurrent/prior build attempt on the same workstation left its own artifacts at
  `/root/moonray-blender/install/deps` and per-repo install dirs; left untouched, unrelated
  to this session's own evidence. See `docs/evidence/phase03/README.md`.
- GPU/XPU: not attempted, not proven. `-DMOONRAY_USE_OPTIX=NO` throughout; no CUDA/OptiX code
  compiled. See `docs/completions/03-moonray-native-runtime.md`'s "GPU/XPU status" section for
  exactly what a future validation phase would need to prove.

## Durable decisions
- Windows 11 workstation host.
- Blender + MoonRay-facing runtime execute under WSL2/WSLg Linux.
- Blender baseline: 5.2.1 LTS until an explicit compatibility migration.
- Direct Blender `RenderEngine` ↔ MoonRay bridge is primary.
- MoonRay initially runs in a separate native Bridge Process for crash/dependency isolation.
- IPC/shared-memory/binary transport is expected; exact protocol is a Phase 04 decision.
- Hydra/hdMoonray is reference/fallback/benchmark only; do not silently restore it as the primary architecture.
- CPU is mandatory first render baseline. XPU/CUDA is a separate evidence gate.
- Do not claim Direct Bridge is faster than Hydra until Phase 10 benchmark evidence exists.

## Verified host facts (Phase 02, observed)
- Distro: `MoonRay-Rocky9`, Rocky Linux 9.8, WSL2, root user, systemd active.
- Distro VHDX: `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9` (beside the repo, 953 GB free).
- Linux-native runtime root: `/root/moonray-blender` with `src/ build/ install/ cache/ tools/ projects/ logs/ tmp/`.
- Blender: 5.2.1 LTS, hash `9e2066aef7ef`, at `/root/moonray-blender/tools/blender-current/blender`.
- Launcher: `~/bin/blender-moonray-host` (forces X11).
- Blender bundled Python 3.13.13; OpenUSD 26.03 as a single `lib/libusd_ms.so`.
- Hardware: Xeon E5-2690 v4 (28 threads), 31.8 GiB host RAM (15 GiB visible to WSL), RTX 3060 12 GB.
- CUDA/OptiX user-mode libraries present in WSL; `nvidia-smi` works.
- Toolchain available: gcc/g++ 11 (el9), cmake, ninja (CRB enabled), git, python3.
- **Known limitation:** WSLg OpenGL is software (`llvmpipe`) — Rocky's Mesa has no `d3d12` Gallium driver. Non-blocking for CPU rendering; a real input to Phase 08.

## Supporting repository infrastructure
- `docs/vendor/openmoonray/` — pinned local mirror of the OpenMoonRay developer-reference documentation (see its `UPSTREAM.json` / `ATTRIBUTION.md`). Reference material only; it does not advance any phase.
- `UPSTREAM_LOCK.json` — pinned OpenMoonRay dependency commits, reconciled against the openmoonray superproject's own submodule gitlinks as of the Phase 03 pre-build audit (2026-09-09), and now built successfully against exactly these commits. Treat as canonical; do not choose new commits ad hoc.
- `configs/moonray-source-lock.json` — minimal machine-readable build manifest derived from `UPSTREAM_LOCK.json`, for the CPU-baseline component subset only.
- `docs/research/03-upstream-pin-audit.md` — the Phase 03 pre-build audit: dependency reconciliation table, full 20-submodule inventory with required/optional/excluded classification, and build risks pulled from real upstream build docs.
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — the original build plan, with a correction note added after real execution (see its top) pointing at what was actually run.
- `scripts/linux/phase03_install_packages.sh`, `phase03_build_deps.sh`, `phase03_build_moonray.sh`, `phase03_render_test.sh` — the actual, executed, reproducible Phase 03 build scripts.
- `docs/completions/03-moonray-native-runtime.md`, `docs/evidence/phase03/` — the Phase 03 Completion Record and evidence.

## Read first
1. `AGENTS.md` / `CLAUDE.md` as applicable.
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md`
6. `docs/completions/03-moonray-native-runtime.md` and `docs/evidence/phase03/` for what Phase 03 actually proved.
7. `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md`
8. `docs/phases/04-direct-bridge-prototype.md` before Phase 04 is approved to start.

## Current assignment — awaiting user approval to start Phase 04
Phase 03 is complete (see above). Phase 04 (smallest native `moonray_bridge` process +
IPC contract, building on the installed runtime at
`/root/moonray-blender/install/openmoonray`) has **not** been started and requires
explicit user approval before any work begins, per the mandatory phase protocol.

## Practical notes for the next session
- Enter the distro with `wsl -d MoonRay-Rocky9`; the project is visible at `/mnt/d/01_DEV/blender-moonray-render-engine`.
- Keep all build trees under `/root/moonray-blender`, never on `/mnt/*`.
- Calling `wsl.exe` from PowerShell 5.1 needs `$env:WSL_UTF8=1` and tolerance for native stderr; see `Invoke-Wsl` in `scripts/windows/phase02_setup_wsl_rocky.ps1`.
- From Git Bash, prefix `wsl.exe` calls with `MSYS_NO_PATHCONV=1` or `/mnt/...` paths get mangled.
- WSL currently sees 15 GiB RAM. This was sufficient for the full Phase 03 build (deps + 4 repositories) at a conservative `-j 8`; no `.wslconfig` tuning was needed.
- One manual cleanup is outstanding: delete `D:\WSL\MoonRay-Rocky9\shortcut.ico`.

## Mandatory phase protocol
1. Execute only the current approved phase.
2. Verify acceptance criteria with observed evidence.
3. Update the phase Completion Record.
4. Write/update `docs/completions/NN-<slug>.md`.
5. Update Architecture/ADR only for material decisions.
6. Mark current phase `[x]` in Roadmap and activate the next phase only per the user's instruction.
7. Overwrite NEXT_SESSION with exact resume state.
8. Stop and ask in Russian: `Phase NN завершён. Переходим к Phase NN+1?`
9. Only after explicit approval execute the next phase.

## Planned sequence after Phase 03
- 04: smallest native bridge + renderer proof + IPC contract.
- 05: Blender `RenderEngine`, first F12 MoonRay frame.
- 06: geometry/transforms/camera/lights.
- 07: materials/textures/instances.
- 08: progressive Rendered Viewport (watch the software-GL limitation).
- 09: final/AOV/animation/EXR.
- 10: incremental updates + direct-vs-Hydra benchmark if Hydra comparison is available.
- 11: recovery/packaging/installer.
- 12: production acceptance/release.

## Reporting
Report observed facts only: Result, Manual check, Files changed, Validation, Important decisions, Remaining risks. Never claim a renderer/build/test works unless actually observed.
