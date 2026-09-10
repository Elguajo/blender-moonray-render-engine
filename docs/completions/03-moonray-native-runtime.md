# Phase 03 Completion — Reproducible Native MoonRay Runtime

Status: COMPLETED
Completed: 2026-09-09
Workstation: `DESKTOP-9O2U790`, distro `MoonRay-Rocky9` (WSL2, Rocky Linux 9.8)

## Outcome
A pinned, CPU-only MoonRay runtime was built from the audited upstream source snapshot
and independently, reproducibly proven to render:

```text
openmoonray superproject b9b0ac29135b26e20a51edf9028558bb64df6700
├── cmake_modules   1b1b7af8111b0a8ceaff45f3c47a778b0ca07ec4
├── scene_rdl2      1229d3eaa1ee41dc1ddefbe781c623edceafbac8
├── mcrt_denoise    0050e726309a533e7964bd05380430e6b06cce7a
├── moonray         eef67ae992b5037943a7716cca96ed443c36dcec
└── moonshine       a3c8667298a23df7d6efed128cb475484de66c8e
```

`moonray -in testdata/rectangle.rdla -out phase03-rectangle.exr` exited 0 and produced a
valid 512x512 RGBA float EXR with non-constant pixel content (see
`docs/evidence/phase03/render-check.txt`). No Hydra/hdMoonray/Arras/USD component was
initialized or built. No CUDA/OptiX code path was compiled (`-DMOONRAY_USE_OPTIX=NO`,
confirmed absent from every configure log). MoonRay XPU/GPU rendering was **not**
attempted and is **not** claimed to work on this or any machine by this phase.

## Delivered
- `scripts/linux/phase03_install_packages.sh` — Rocky 9 OS package install (`--nocuda --noqt --nocgroup`).
- `scripts/linux/phase03_build_deps.sh` — third-party dependency build (`-DNO_USD=1`).
- `scripts/linux/phase03_build_moonray.sh` — the 4 required MoonRay repositories, built and installed separately (see below for why).
- `scripts/linux/phase03_render_test.sh` — fresh-shell runtime verification + minimal CPU render + EXR checks.
- `docs/evidence/phase03/` — preflight, source-pin re-verification, configure summary, runtime check, render check, and a README explaining two real issues found during execution (below).
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — corrected in place with a note on the approach change; original plan text kept for record.

## Observed verification
| Check | Result |
|---|---|
| Superproject + 5 required submodule SHAs match the pinned lock | PASS — re-verified independently after checkout and again after a clean rebuild |
| Build stays on Linux-native filesystem (not `/mnt/*`) | PASS — `/root/moonray-blender` on ext4 `/dev/sdd`; scripts also assert this at runtime |
| OS packages installed with `--nocuda --noqt --nocgroup` | PASS — CUDA repo/packages never added, Qt5 never installed |
| Third-party deps built with `-DNO_USD=1` | PASS — no USD build attempted; confirmed by directory contents |
| MoonRay-family CMake configure shows no CUDA/OptiX probing | PASS — zero "CUDA"/"OPTIX" lines in `moonray`/`mcrt_denoise` configure logs |
| `moonray` binary installed, `ldd` fully resolved | PASS — zero "not found" libraries |
| `moonray -help` runs | PASS |
| Standalone CPU render of `testdata/rectangle.rdla` | PASS — exit 0, valid EXR, non-constant pixel stats, no NaN/Inf |
| Fresh-shell reproducibility (2 independent runs) | PASS — identical pixel statistics both times |
| Clean rebuild from empty build/install dirs | PASS — see "Problems discovered and fixed" |
| Hydra/hdMoonray/Arras/USD never initialized or built | PASS — confirmed by submodule/directory inspection, not assumed |

## Decisions made
- **Per-repository builds instead of the monolithic `--preset rocky9-release` superproject build.** The prepared runbook assumed the preset; inspecting the real pinned `CMakeLists.txt` files first (mandated before running anything) found unconditional `add_subdirectory()` calls into uninitialized Hydra/Arras/USD-dependent submodules with no guard. Upstream's own documented "Building the Repositories Separately" procedure was used instead. Same source pins, different build mechanics — not a source-pin or architecture change.
- **Third-party dependency install root left at its upstream default, `/opt/MoonRay/installs`**, rather than relocated under `/root/moonray-blender/install/`. The main build's `CMakePresets.json` hardcodes this path as a literal environment default (`DEPS_ROOT`) in a vendored preset file; relocating it would require editing pinned upstream source. `/opt` is still Linux-native ext4 (not a Windows mount), so the project's actual constraint ("never build under `/mnt/*`") is satisfied; only the specific `/root/moonray-blender/...` naming convention for this one disposable dependency cache was not followed. MoonRay's own source, build, and final install (`/root/moonray-blender/{src,build,install}/openmoonray`) all do follow the project's designated tree.
- **`-DNO_USD=1`** on the third-party dependency build, skipping a Pixar USD source build entirely — nothing in the required build graph needs it once Hydra/hdMoonray is excluded, and it is a very large, slow build step.
- **`--nocgroup`** on `install_packages.sh` — `libcgroup` is only used by Arras distributed-rendering nodes, which are excluded from this project's local single-process CPU baseline.

## Problems discovered and fixed
Real execution surfaced defects; each was fixed rather than worked around, per phase protocol.

1. **Wrapper script `set -u` incompatible with the pinned `install_packages.sh`.** The vendored script references `${LD_LIBRARY_PATH}` unconditionally; a fresh shell has it unset. Fixed in `phase03_install_packages.sh` (pre-seed a default, `nounset` relaxed for that one sourced call) — the vendored upstream script itself was left unmodified.
2. **The prepared plan's `cmake --preset rocky9-release` against the openmoonray superproject would not have configured cleanly**, and if forced to by initializing every submodule, would have pulled in the full Hydra/hdMoonray + Pixar USD + Arras stack this phase must not touch. See "Decisions made" above and `docs/evidence/phase03/README.md` for the full evidence trail (exact `CMakeLists.txt` lines cited there).
3. **A stale `CMakeCache.txt` from an apparently concurrent, independent build attempt on the same workstation caused the first successful build to link against a dependency install location (`/root/moonray-blender/install/deps`) this session had not itself built**, because reconfiguring an existing CMake build directory does not re-read already-cached variables from the environment. Detected by inspecting `ldd` output against what this session's own `phase03_build_deps.sh` had produced. Fixed by deleting this session's own build/install directories and rebuilding from a genuinely empty state; the clean rebuild's `ldd` output confirms every third-party library now resolves under this session's own `/opt/MoonRay/installs`. Full account in `docs/evidence/phase03/README.md`. This did not indicate any problem with the pinned source or the render result itself — both binaries rendered identical pixel statistics — but the clean rebuild is what this Completion Record's evidence is based on.
4. **The pre-build audit's classification of `moonshine` as "required only if Phase 07 chooses `DwaBaseMaterial`" was too weak** — the canonical upstream test scene `testdata/rectangle.rdla` itself uses `DwaBaseMaterial`, making `moonshine` a hard requirement for this phase's own render test, independent of any future Phase 07 decision.
5. **Resolved without incident, contrary to a build risk flagged by the audit**: `mcrt_denoise`'s CUDA/OptiX/OptiX dependency is gated by the exact same `MOONRAY_USE_OPTIX` flag as the main build (confirmed by reading `mcrt_denoise/CMakeLists.txt` directly) — no separate flag was needed.
6. **Resolved without incident**: Rocky 9.8's system CMake (3.31.8) already exceeds the upstream-required minimum (3.23.1); the `install_packages.sh` script's own redundant download of CMake 3.23.1 into `/installs` is harmless and unused (nothing on `PATH` references it).

## Deviations / technical debt
- The apparent concurrent build attempt (see problem #3) left its own artifacts at `/root/moonray-blender/install/deps` and `/root/moonray-blender/install/{scene_rdl2,mcrt_denoise,moonray,moonshine}`, which were not touched or removed (not this session's to delete). They do not affect this Completion Record's evidence, which is entirely from this session's own `/opt/MoonRay/installs` + `/root/moonray-blender/install/openmoonray` tree.
- No `.wslconfig` memory/parallelism tuning was needed — the conservative `-j 8` default completed the full build (deps + 4 repositories) in well under 30 minutes total on 15 GiB WSL RAM, with no OOM/swap pressure observed.
- A full from-scratch rebuild of the third-party dependency chain itself (not just the 4 MoonRay repositories) was not repeated after the cache-contamination fix, since that dependency build was never implicated (it writes to its own, never-shared `/opt/MoonRay/installs` path) — only the 4 MoonRay-repository build directories showed cache reuse from the other session.
- `moonray_gui`, `render_profile_viewer`, `rats`, `materialx_shaders`, and Arras/Hydra/USD components remain un-built, as scoped.

## Architectural impact
None. ADR-0002 (Direct MoonRay Bridge primary; Hydra/hdMoonray reference-only) is
unaffected — Hydra/hdMoonray was never built or touched, consistent with that decision.
No evidence from this phase argues for or against the architecture; it only proves the
CPU renderer itself builds and runs standalone, independent of any Blender integration.

## GPU/XPU status carried forward
Unchanged from Phase 02/the Phase 03 pre-build audit and `docs/research/04-prior-blender-moonray-implementations.md`:
CPU is the only proven render path on this machine. `-DMOONRAY_USE_OPTIX=NO` was used
throughout; no CUDA/OptiX code was compiled; no NVIDIA GPU capability claim is made or
implied by this phase. A dedicated future validation phase would still need to prove,
in order: an OptiX-enabled build actually compiles here, the GPU accelerator actually
initializes at runtime under WSL2 (independently reported as failing for OptiX on WSL2
in OpenMoonRay's own community discussions), and a render actually executes via
`-exec_mode xpu` rather than silently falling back to CPU.

## Follow-up
Phase 04: smallest native `moonray_bridge` process + IPC contract + renderer proof,
building on this phase's installed runtime at `/root/moonray-blender/install/openmoonray`.
Not started by this phase.
