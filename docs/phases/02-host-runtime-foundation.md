# Phase 02 — Windows/WSL/Linux GPU and GUI Foundation

## Goal
Create a reproducible WSL2 Linux host on the actual Windows 11 workstation and prove that Blender 5.2.1 LTS Linux can run through WSLg with the filesystem, OpenUSD/Python environment, and GPU visibility needed before MoonRay is built.

## Context
Phase 01 accepted WSL2/WSLg as the production execution boundary. Rocky Linux 9 is preferred because MoonRay currently tests it upstream. CPU rendering is the first required MoonRay target; CUDA visibility is measured now but XPU compatibility is not claimed in this phase.

## Context hints
- `docs/project/ARCHITECTURE.md`
- `docs/decisions/ADR-0001-wsl2-linux-blender-hydra-host.md`
- `docs/research/01-compatibility-matrix.md`
- `docs/completions/01-compatibility-and-host-architecture.md`

## In scope
- Inventory Windows, WSL, CPU, RAM, GPU and driver versions relevant to the stack.
- Update/verify WSL2 and WSLg health.
- Establish an isolated Rocky Linux 9.x WSL distro if viable; otherwise document blocker before considering the distro fallback.
- Define Linux-native project/source/build/install/cache paths.
- Verify basic GUI acceleration through WSLg.
- Install/run Blender 5.2.1 LTS Linux in the WSL environment.
- Verify Blender version/platform, basic `.blend` read/write, bundled Python and bundled `pxr`/USD identity.
- Verify NVIDIA/CUDA device visibility when NVIDIA hardware is present.
- Produce a reproducible host-environment record and operator start/stop commands.

## Out of scope
- Building MoonRay or Direct Bridge.
- Registering a MoonRay Hydra delegate in Blender.
- Claiming MoonRay XPU support from CUDA visibility alone.
- Production scene translation tests.

## Prepared execution assets
- `scripts/windows/phase02_setup_wsl_rocky.ps1` — Windows/WSL/Rocky bootstrap + Windows evidence.
- `scripts/linux/phase02_setup_host.sh` — Rocky host dependencies + pinned Blender 5.2.1 install.
- `scripts/linux/phase02_verify_host.sh` — automated WSL/graphics/Blender/USD/.blend verification.
- `docs/runbooks/PHASE02_HOST_SETUP.md` — operator runbook.
- `docs/evidence/phase02-host-evidence.template.md` — durable evidence template.

Execution state: **prepared, awaiting real-workstation run**. The phase must not be marked complete until the verifier and GUI smoke test pass on the user's Windows workstation.

## Tasks
- [ ] Capture workstation and WSL inventory.
- [ ] Establish/update WSL2 + WSLg baseline.
- [ ] Establish isolated Rocky Linux 9.x distro and verify system basics.
- [ ] Create production-safe Linux filesystem layout.
- [ ] Verify WSLg GUI and graphics path.
- [ ] Install/pin Blender 5.2.1 LTS Linux.
- [ ] Verify Blender GUI launch, version, test file I/O and bundled Python.
- [ ] Inspect Blender bundled OpenUSD identity/namespace evidence from the running host.
- [ ] Verify GPU/CUDA visibility without yet enabling MoonRay XPU.
- [ ] Record exact host/runtime versions and recovery steps.

## Acceptance criteria
- [ ] Exact Windows build, WSL version/kernel, distro release, Blender version, CPU/RAM/GPU/driver inventory is recorded.
- [ ] WSL2 distro starts/stops reproducibly without modifying the user's primary Windows Blender installation.
- [ ] WSLg launches Blender 5.2.1 Linux successfully.
- [ ] Blender can create, save, close and reopen a minimal `.blend` from the chosen Linux-native project path.
- [ ] Blender's runtime exposes enough `pxr`/USD information to confirm the host dependency identity needed for Phase 03.
- [ ] If NVIDIA GPU exists, WSL can identify the device/driver and run a minimal CUDA visibility check; failure is recorded without blocking the CPU baseline unless it breaks Blender/WSLg.
- [ ] Build/source/install/cache directories are separated and documented.
- [ ] Reproduction and rollback/start-stop instructions are written.

## Negative / security cases
- Do not install a Linux NVIDIA display driver inside WSL; use the Windows NVIDIA driver path documented by NVIDIA.
- Do not put build trees on `/mnt/c` by default; use Linux-native storage unless evidence justifies otherwise.
- Do not modify the user's production Windows Blender installation.
- Do not globally replace Blender's bundled Python/USD libraries.
- Do not run MoonRay build scripts in this phase.

## Verification
- WSL version/kernel/distro commands captured in the completion report.
- GUI launch evidence for Blender 5.2.1.
- Blender Python console or background-script evidence for version/platform/USD identity.
- Minimal `.blend` round-trip.
- GPU/CUDA visibility evidence when applicable.
- Filesystem layout and start/stop commands manually checked.

## Completion Record
Populate only when this phase becomes [x].
