# Phase 02 Host Evidence

Status: OBSERVED PASS
Captured: 2026-09-09
Workstation: `DESKTOP-9O2U790`
Raw evidence: `docs/evidence/phase02/windows-host.txt`, `docs/evidence/phase02/linux-host.txt`, `docs/evidence/phase02/blender-wslg-gui.png`

## Windows
- Windows edition/build: build `10.0.26100.9445` (24H2 servicing baseline). `Get-ComputerInfo` reports `WindowsProductName = Windows 10 Pro` / `WindowsVersion = 2009`; those two fields read the legacy `ProductName`/`ReleaseId` registry values, which Windows 11 does not update. Build 26100 is the authoritative identifier.
- CPU: Intel Xeon E5-2690 v4 @ 2.60 GHz — 14 cores / 28 threads
- RAM: 34 193 002 496 bytes (~31.8 GiB)
- GPU: NVIDIA GeForce RTX 3060, 12 288 MiB
- Display driver: NVIDIA 610.88 (KMD), CUDA UMD 13.3

## WSL
- WSL version: 2.6.3.0
- Kernel: 6.6.87.2-1 (`6.6.87.2-microsoft-standard-WSL2`)
- WSLg version: 1.0.71
- MSRDC: 1.2.6353 · Direct3D: 1.611.1-81528511 · DXCore: 10.0.26100.1
- Distro name: `MoonRay-Rocky9`
- WSL generation: 2
- Distro VHDX location: `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9` (beside the repository, not inside it)
- Pre-existing `Ubuntu` and `docker-desktop` distros untouched

## Rocky Linux
- Release: Rocky Linux 9.8 (Blue Onyx), `VERSION_ID="9.8"`, support end 2032-05-31
- Architecture: x86_64
- Image: `Rocky-9-WSL-Base-9.8-20260525.0.x86_64.wsl`
- Image SHA256: `58de2455cd475abbaa3cef0f9d240f405c379b5a54d3826f9b55cc41e3829221` — verified against the checksum published alongside the image
- systemd: active (PID 1 is `systemd`)
- Default user: `root`
- Linux-native runtime root: `/root/moonray-blender` on `/dev/sdd`, 1007 GB total / 953 GB available
- vCPUs visible: 28 · RAM visible: 15 GiB · Swap: 4 GiB

## Blender
- Version: `Blender 5.2.1 LTS`, build hash `9e2066aef7ef`, branch `blender-v5.2-release`, built 2026-08-25
- Archive: `blender-5.2.1-linux-x64.tar.xz`
- Archive SHA256: `a31f524fa99a527d3d52b7f5aaa68c34e1a19d5a1c9473f79c5cc610fd5b10e9` — verified against Blender's official `blender-5.2.1.sha256`
- GUI via WSLg: PASS — window opened, splash dismissed, viewport interactive, object selection and popup menus render correctly. See `blender-wslg-gui.png`.
- Windowing baseline: X11 via WSLg (launcher clears `WAYLAND_DISPLAY`). Blender logs `Unable to find 'libwayland-cursor.so'` — expected and harmless on the forced-X11 path.
- WSLg window title reports `[WARN:COPY MODE]`, consistent with the software OpenGL path below.
- Bundled Python: 3.13.13 (GCC 14.2.1, Red Hat 14.2.1-11)
- OpenUSD version: `Usd.GetVersion() == (0, 26, 3)` → OpenUSD 26.03, matching the Phase 01 research finding
- pxr module identity/path: `/root/moonray-blender/tools/blender-5.2.1/5.2/python/lib/python3.13/site-packages/pxr/__init__.py`
- Bundled USD shared library: `/root/moonray-blender/tools/blender-5.2.1/lib/libusd_ms.so` — a single monolithic build, relevant to any future Hydra/USD-linking work

## Graphics
- DISPLAY: `:0` · WAYLAND_DISPLAY: `wayland-0` · `/dev/dxg` present
- GL renderer: `llvmpipe (LLVM 21.1.8, 256 bits)`, Mesa 25.2.7, `Accelerated: no`
- Vulkan: instance 1.4.328; only device is `llvmpipe`, `PHYSICAL_DEVICE_TYPE_CPU`
- NVIDIA visible in WSL: PASS — `nvidia-smi` 610.57.01 reports the RTX 3060
- CUDA driver visibility: `/usr/lib/wsl/lib/libcuda.so.1`, `libnvoptix.so.1`, `libnvidia-ml.so.1` present

## File I/O
- Smoke file: `/root/moonray-blender/projects/phase02-smoke/phase02-roundtrip.blend`
- Save: PASS
- Reopen: PASS
- Object-state assertion: PASS (`PHASE02_SMOKE_CUBE` present after reload)

## Automated result
- PASS: 11
- WARN: 1
- FAIL: 0
- `PHASE02_RESULT=PASS`

## Blocking issues
None.

## Non-blocking warnings

### W1 — WSLg OpenGL is software-rendered (llvmpipe)
WSL supplies `/usr/lib/wsl/lib/libd3d12.so` and `libd3d12core.so`, but Rocky's `mesa-dri-drivers-25.2.7-4.el9` does not ship the `d3d12` Gallium driver (`/usr/lib64/dri` contains `zink_dri.so` but no `d3d12_dri.so`, and no Vulkan GPU device exists to back zink). OpenGL therefore falls back to `llvmpipe`.

Impact assessment:
- Does **not** affect the Phase 02 acceptance criteria: the GUI launches and is interactive.
- Does **not** affect MoonRay's CPU render baseline, which is the mandatory first target.
- Does **not** affect the CUDA/OptiX compute path — `libcuda.so.1` and `libnvoptix.so.1` are present and `nvidia-smi` works, so a future XPU evaluation is not blocked by this.
- **Does** affect Blender's own viewport drawing performance, which is a material input to Phase 08 (Interactive Rendered Viewport).

Possible mitigations, none of them attempted or verified in this phase: a Mesa build that includes the `d3d12` Gallium driver, or accepting software GL for the DCC viewport. This must be measured in Phase 08 rather than assumed either way.

## Reproduction

```powershell
.\scripts\windows\phase02_setup_wsl_rocky.ps1
```

```bash
wsl -d MoonRay-Rocky9
bash scripts/linux/phase02_setup_host.sh
bash scripts/linux/phase02_verify_host.sh
blender-moonray-host
```

## Rollback

```powershell
wsl --unregister MoonRay-Rocky9
```

Removes the distro and its VHDX. The Windows Blender installation, the `Ubuntu` distro and `docker-desktop` are unaffected.

## Manual cleanup outstanding
`D:\WSL\MoonRay-Rocky9\shortcut.ico` (4.6 KB) remains from the pre-move distro location. Removing `D:\WSL` was blocked by the agent sandbox; delete it manually.
