# Phase 02 Completion — Windows/WSL/Linux GPU and Blender GUI Foundation

Status: COMPLETED
Completed: 2026-09-09
Workstation: `DESKTOP-9O2U790`

## Outcome
The production host boundary defined by ADR-0001 was built and verified on the real workstation:

```text
Windows 11 (build 10.0.26100.9445)
└── WSL 2.6.3.0 + WSLg 1.0.71, kernel 6.6.87.2
    └── Rocky Linux 9.8 (Blue Onyx) — distro "MoonRay-Rocky9"
        └── Blender 5.2.1 LTS Linux
```

The automated verifier ended `PHASE02_RESULT=PASS` (11 PASS / 1 WARN / 0 FAIL) and the Blender GUI was observed running interactively through WSLg. MoonRay and the Direct Bridge were not built, as required by the phase scope.

## Delivered
- Isolated WSL2 distro `MoonRay-Rocky9` from the pinned, checksum-verified Rocky 9.8 WSL image.
- Linux-native runtime layout under `/root/moonray-blender` (`src`, `build`, `install`, `cache`, `tools`, `projects`, `logs`, `tmp`).
- Pinned Blender 5.2.1 LTS Linux, installed from a checksum-verified official archive.
- Operator launcher `~/bin/blender-moonray-host` (forces X11 through WSLg for the first baseline).
- Persisted evidence: `docs/evidence/phase02-host-evidence.md`, plus raw `docs/evidence/phase02/windows-host.txt`, `docs/evidence/phase02/linux-host.txt` and the GUI screenshot `docs/evidence/phase02/blender-wslg-gui.png`.
- Updated operator runbook `docs/runbooks/PHASE02_HOST_SETUP.md`.

## Observed verification
| Check | Result |
|---|---|
| Running under WSL2 | PASS |
| Rocky Linux 9.x | PASS — 9.8 (Blue Onyx) |
| WSLg `DISPLAY=:0` | PASS |
| `/dev/dxg` vGPU device | PASS |
| Build/runtime root is Linux-native | PASS — `/root/moonray-blender`, not `/mnt/*` |
| NVIDIA visible in WSL | PASS — `nvidia-smi` 610.57.01, RTX 3060 |
| Pinned Blender 5.2.1 | PASS — hash `9e2066aef7ef` |
| Blender bundled Python imports `pxr`/USD | PASS — USD `(0, 26, 3)`, Python 3.13.13 |
| Bundled OpenUSD library located | PASS — `lib/libusd_ms.so` |
| `.blend` create/save | PASS |
| `.blend` reopen + object-state assertion | PASS |
| WSLg OpenGL acceleration | **WARN — software `llvmpipe`** |
| Blender GUI launch through WSLg | PASS — observed, screenshot persisted |

Both downloaded artifacts were checksum-verified against upstream-published values:
- Rocky image `58de2455cd475abbaa3cef0f9d240f405c379b5a54d3826f9b55cc41e3829221`
- Blender archive `a31f524fa99a527d3d52b7f5aaa68c34e1a19d5a1c9473f79c5cc610fd5b10e9`

## Decisions made
- **Distro VHDX lives beside the repository**, at `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9`, not on `C:` (58.9 GB free) and not inside the repository tree. Phase 03 builds MoonRay and needs headroom; the volume offers 953 GB. The filesystem inside the VHDX is Linux-native ext4, so the "no `/mnt/c` build trees" rule still holds. User-approved.
- **X11 is the first windowing baseline** through WSLg; Wayland stays a separately testable variable.
- **Software OpenGL is accepted for Phase 02** and recorded as a non-blocking warning rather than a blocker, because the phase requires the GUI to launch, not to be GPU-accelerated.
- **CRB repository enabled** in the Rocky distro so `ninja-build` is available for the Phase 03 CMake build.

## Problems discovered and fixed
The prepared scripts had never been executed on real hardware. Executing them surfaced defects that were repaired rather than worked around:

1. `phase02_setup_wsl_rocky.ps1` aborted unless run elevated, even though WSL was already installed and healthy. Elevation is now demanded only when WSL itself must be installed or updated.
2. The same script wrote UTF-16LE `wsl.exe` output into the evidence file, corrupting it. `WSL_UTF8=1` now forces UTF-8.
3. Under PowerShell 5.1, `$ErrorActionPreference = "Stop"` turned benign `wsl.exe` stderr (`Failed to get unit file state for cloud-init.service`) into a terminating error, failing the script after a *successful* distro install. Native `wsl.exe` calls now run through an `Invoke-Wsl` helper judged by `$LASTEXITCODE`.
4. `ValueFromRemainingArguments` mis-bound `-d` and swallowed the `--` separator, so the Rocky probe ran the distro name as a shell command. Arguments are now passed as an explicit array.
5. The script never recorded where the VHDX actually lives; it now reads the real path from the registry and flags a mismatch.
6. `phase02_setup_host.sh` assumed `sudo` exists, but the Rocky WSL base image logs in as `root`. It now detects root vs. sudo.
7. A single unavailable optional package aborted the entire host bootstrap. Core packages are now blocking; diagnostic extras are individually installed and downgraded to warnings.
8. **`libSM` and `libICE` were missing from the package list, so Blender could not start at all** (`error while loading shared libraries: libSM.so.6`). Both added to the core set.
9. `phase02_verify_host.sh` invoked Blender without `--python-exit-code`. Blender exits 0 when a `--python-expr` script raises, so a failed `pxr` import or a failed round-trip assertion would have been recorded as `[PASS]`. This was the most serious defect: the verifier could have certified criteria that had actually failed.
10. The verifier used `exec > >(tee ...)`, which can truncate the evidence file on exit. Replaced with a piped subshell preserving the exit code via `PIPESTATUS`.
11. The verifier collected no OpenUSD library identity and did not classify the OpenGL renderer. Both are now explicit checks.

## Deviations / technical debt
- `D:\WSL\MoonRay-Rocky9\shortcut.ico` (4.6 KB) remains from the pre-move distro location; deletion was blocked by the agent sandbox and needs one manual removal.
- WSL sees 15 GiB of the host's 31.8 GiB and 28 vCPUs. No `.wslconfig` tuning was applied; Phase 03 should decide whether the MoonRay build needs more memory.
- Wayland was not tested.

## Architectural impact
None. ADR-0001 (WSL2/WSLg boundary) and ADR-0002 (Direct Bridge primary) are both unaffected — no evidence in this phase contradicts either. Architecture was therefore not modified.

Two facts carry forward as Phase 03 inputs:
- Blender 5.2.1 bundles OpenUSD 26.03 as a single monolithic `libusd_ms.so`. This constrains any future work that links against Blender's USD, which under ADR-0002 is the Hydra fallback path rather than the primary one.
- The CUDA/OptiX user-mode driver stack is present in WSL, so a later XPU evaluation is not blocked by the host. This is **not** a claim that MoonRay XPU works.

## Follow-up
Phase 03: build a pinned, reproducible native MoonRay runtime inside this verified environment and prove a minimal CPU render. No Hydra dependency, no Blender integration.

Open risk to carry into Phase 08: Blender's viewport currently draws through software OpenGL. This must be measured, not assumed, when the interactive Rendered Viewport is built.
