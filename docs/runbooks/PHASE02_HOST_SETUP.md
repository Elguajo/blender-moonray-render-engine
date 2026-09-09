# Phase 02 Runbook — Host Runtime Foundation

## Purpose

Establish the pinned production host boundary:

```text
Windows 11
└── WSL2 + WSLg
    └── Rocky Linux 9.8 x86_64
        └── Blender 5.2.1 LTS Linux
```

MoonRay and the Direct Bridge are intentionally not installed in this phase.

## Safety rules

- Keep the existing Windows Blender installation untouched.
- Do not install an NVIDIA Linux display driver inside WSL. NVIDIA documents that the Windows driver is the driver used by WSL.
- Keep source/build/install/cache/project trees in the Linux filesystem (`~/moonray-blender`), not under `/mnt/c`.
- CPU is the required renderer baseline. NVIDIA/CUDA visibility is evidence only; it does not claim MoonRay XPU support.
- Blender 5.2.1 is pinned. Do not auto-upgrade it during this validation.

## Step A — Windows

1. Save the project folder locally.
2. Open PowerShell. **Administrator is required only if WSL itself is not yet installed or needs `wsl --update`.** If `wsl --version` already reports a version, the script runs unelevated and skips the platform-level steps.
3. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd <path-to-project>
.\scripts\windows\phase02_setup_wsl_rocky.ps1
```

The script captures inventory, verifies/updates WSL, downloads the versioned Rocky 9.8 WSL image, verifies Rocky's published SHA256, installs `MoonRay-Rocky9`, records the distro's actual VHDX location, and writes Windows-side evidence.

If Windows requests a reboot after first enabling WSL, reboot and run the same script again.

### Distro storage location

The distro's ext4 VHDX defaults to `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9` — beside the repository, not inside it, so archiving or copying the project never drags a multi-hundred-GB VHDX along. Override with:

```powershell
.\scripts\windows\phase02_setup_wsl_rocky.ps1 -DistroLocation "E:\somewhere\MoonRay-Rocky9"
```

To relocate an already-installed distro:

```powershell
wsl --manage MoonRay-Rocky9 --move "D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9"
```

The filesystem inside the VHDX is Linux-native ext4 regardless of which Windows volume hosts the file. This is not a `/mnt/c` build tree.

## Step B — Rocky Linux

Open the distro:

```powershell
wsl -d MoonRay-Rocky9
```

The Rocky WSL base image logs in as `root`; the setup script uses `sudo` only when it is not already root.

From the project directory as seen by WSL, run:

```bash
bash scripts/linux/phase02_setup_host.sh
bash scripts/linux/phase02_verify_host.sh
```

The Linux setup installs only host/build/graphics utilities and Blender 5.2.1. It does **not** install MoonRay, the Direct Bridge, CUDA Toolkit, or an NVIDIA Linux driver.

Core packages are treated as blocking; optional diagnostic packages (`vulkan-tools`, `glx-utils`, …) are installed individually and reported as non-blocking warnings if a repo does not carry them.

## Step C — GUI smoke test

Launch:

```bash
blender-moonray-host
```

The Phase 02 launcher deliberately forces X11 (`WAYLAND_DISPLAY=""`) for the first production baseline. Blender 5.2 supports both X11 and Wayland; Wayland can be tested later as a separate variable.

Manual PASS conditions:
- Blender window opens through WSLg;
- viewport responds normally;
- File → About Blender reports 5.2.1;
- existing Windows Blender/configuration remains untouched.

## Step D — Evidence

Automated Linux evidence:

```text
~/moonray-blender/logs/phase02-host-evidence.txt
```

Windows-side evidence:

```text
docs/evidence/phase02/windows-host.txt
```

Persisted phase evidence:

```text
docs/evidence/phase02-host-evidence.md
```

Stop all WSL instances:

```powershell
wsl --shutdown
```

Restart this distro:

```powershell
wsl -d MoonRay-Rocky9
```

Remove the distro entirely (rollback):

```powershell
wsl --unregister MoonRay-Rocky9
```

This deletes the VHDX and leaves the Windows Blender installation and all other distros untouched.

## Completion gate

Phase 02 becomes COMPLETE only after:
1. verifier ends with `PHASE02_RESULT=PASS`;
2. Blender GUI opens successfully via WSLg;
3. exact Windows/WSL/Rocky/Blender/USD/GPU evidence is persisted;
4. warnings are classified as blocking or non-blocking.

Do not proceed to MoonRay build solely because these scripts exist.
