# Phase 02 Research — Host Runtime Baseline

## Verified baseline (2026-09-09)

- Windows host: Windows 11 with current Store-delivered WSL/WSLg.
- WSL installation/update path: `wsl --install`, `wsl --update`, WSL2 only for GUI apps.
- Rocky Linux: official Rocky 9 WSL images are supported; pinned image for this phase is `Rocky-9-WSL-Base-9.8-20260525.0.x86_64.wsl`.
- Rocky install path: official Rocky documentation supports `wsl --install --from-file <image.wsl> <machine-name>`.
- Blender: official Linux 5.2.1 LTS binary dated 2026-08-25; Linux requires glibc 2.28+, OpenGL 4.3 and Vulkan 1.3-capable graphics path.
- Blender Linux window systems: X11 and Wayland are both supported. Phase 02 initially forces X11 through WSLg to reduce variables during NVIDIA/WSLg bring-up.
- NVIDIA/WSL: install/update the NVIDIA Windows driver only. Do not install a Linux NVIDIA display driver inside WSL. WSL exposes the Windows CUDA driver to Linux; CUDA Toolkit installation is deferred to a later XPU validation gate.
- OpenUSD identity check: `from pxr import Usd; Usd.GetVersion()` is a valid runtime check. Phase 02 runs it inside Blender's bundled Python rather than system Python.

## Production filesystem rule

Keep all renderer-facing source/build/install/cache/project data under the WSL ext4 filesystem:

```text
~/moonray-blender/
├── src/
├── build/
├── install/
├── cache/
├── tools/
├── projects/
└── logs/
```

Do not use `/mnt/c` for build trees by default. The project/runbook itself may be opened from a Windows-mounted path to start the bootstrap, but the production runtime and future builds live on the Linux filesystem.

## Phase 02 validation boundary

Phase 02 proves only:

```text
Windows 11
  -> WSL2/WSLg
    -> Rocky 9.8
      -> Blender 5.2.1 Linux
        -> Blender bundled Python/OpenUSD
        -> basic GL/Vulkan GUI path
        -> NVIDIA device visibility when present
```

It does not prove MoonRay runtime/Direct Bridge rendering or XPU support.

## Primary sources

- Microsoft WSL install/basic commands and WSL GUI-app documentation.
- Rocky Linux official WSL import documentation and Rocky 9.8 image repository.
- Blender official 5.2 download, requirements, and Linux windowing documentation.
- NVIDIA CUDA on WSL User Guide.
