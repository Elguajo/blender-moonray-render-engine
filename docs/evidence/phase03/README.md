# Phase 03 Evidence — Native MoonRay CPU Runtime

Observed 2026-09-09 inside the `MoonRay-Rocky9` WSL2 distro. This directory holds
concise, git-safe evidence extracted from the real build/run. Full raw logs stay
WSL-native under `/root/moonray-blender/logs/phase03-build/` (paths and checksums
below) and are not committed here — several exceed tens of KB and none are needed
verbatim to verify the acceptance criteria.

## Files
- [`preflight.txt`](preflight.txt) — host/toolchain facts observed before any build step.
- [`source-pins.txt`](source-pins.txt) — independent post-checkout SHA verification.
- [`configure-summary.txt`](configure-summary.txt) — CMake configure excerpts, flags, compiler.
- [`runtime-check.txt`](runtime-check.txt) — `ldd`/`-help` verification of the installed binary.
- [`render-check.txt`](render-check.txt) — the minimal CPU render, exit code, EXR metadata and pixel statistics.

## Why per-repository builds instead of the prepared runbook's monolithic preset
The prepared plan (`docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md`, as originally written)
assumed `cmake --preset rocky9-release` against the `openmoonray` superproject root.
Inspecting the actual pinned `CMakeLists.txt` files before running anything (per the
mandated Step 3) found that the superproject's own top-level `CMakeLists.txt` and
`moonray/CMakeLists.txt` call `add_subdirectory()` **unconditionally** (no option or
`EXISTS` guard) on `rats`, `arras/arras4_core`, `arras/distributed`, `hydra`,
`moonray_arras`, `moonray_dcc_plugins`, `moonshine_usd` and `render_profile_viewer` —
none of which this project initializes or wants (Hydra/hdMoonray, Arras distributed
rendering and USD are all explicitly out of scope per ADR-0002 and this phase's own
instructions). Configuring the monolithic preset as originally planned would have
either hard-failed (uninitialized submodule directories have no `CMakeLists.txt`) or,
if those submodules were fetched just to satisfy the directory walk, would have forced
building the full Pixar USD stack and Hydra plugin — exactly what Phase 03 must not
touch.

Upstream itself documents a supported alternative for this situation
(`building/general_build.md`, "Building the Repositories Separately"): configure each
required repository against its own `CMakeLists.txt`, pointing `CMAKE_MODULE_PATH` at
the separately-cloned `cmake_modules` repo and chaining install prefixes via
`CMAKE_PREFIX_PATH`. This is exactly the audited required-component set
(`cmake_modules`, `scene_rdl2`, `mcrt_denoise`, `moonray`, `moonshine`) and never
touches Hydra/Arras/USD at all. `scripts/linux/phase03_build_moonray.sh` was written
against this approach instead, and `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` was
updated to match. This is a build-approach correction, not a source-pin change — the
same pinned commits were used throughout.

Also discovered while inspecting the same files: the canonical test scene
`testdata/rectangle.rdla` uses `DwaBaseMaterial`, which is provided by `moonshine` — so
`moonshine` is a hard requirement for the minimal render test itself, not merely an
optional Phase 07 concern as the pre-build audit had assumed.

## A concurrent build attempt was found on the same workstation, and how it was handled
Before this session's own build steps ran, the `openmoonray` source was already cloned
(a `git clone` step reported "already cloned" rather than performing a fresh clone),
and a set of build/install logs and directories with different names/paths than this
session's own scripts already existed under `/root/moonray-blender/{logs,build,install}`
(e.g. an install tree at `/root/moonray-blender/install/deps` and separate per-repo
install directories, vs. this session's single shared
`/root/moonray-blender/install/openmoonray` and `/opt/MoonRay/installs`). This is
consistent with another session (this project explicitly supports being followed and
continued from another device/session) having already run a similar build attempt on
this machine, independently of this conversation.

This session's own first full build run (via `scripts/linux/phase03_build_moonray.sh`)
completed successfully and rendered correctly, but a check of the resulting binary's
linked libraries (`ldd`) showed it had picked up dependencies from
`/root/moonray-blender/install/deps` rather than the `/opt/MoonRay/installs` location
this session's own `phase03_build_deps.sh` had just built. The cause: `build/scene_rdl2`
(and the other three build directories) already existed with a `CMakeCache.txt` from
that earlier attempt, and re-running `cmake -S -B` against an **existing** build
directory reuses already-cached variables — this session's own `CMAKE_PREFIX_PATH`
environment variable had no effect on a variable CMake had already cached from before.

To remove this ambiguity, `/root/moonray-blender/build/{scene_rdl2,mcrt_denoise,moonray,
moonshine}` and `/root/moonray-blender/install/openmoonray` were deleted (the other
session's own `/root/moonray-blender/install/deps` and per-repo install directories were
left untouched, since they are not this session's to remove) and the full build was
re-run from a genuinely clean state. The clean rebuild's `ldd` output confirms every
third-party library now resolves under `/opt/MoonRay/installs` (this session's own
dependency build) with zero unresolved libraries, and the render was re-verified against
this clean binary. **All PASS evidence in this Completion Record is from the clean
rebuild**, not the earlier ambiguous one. Both binaries rendered the test scene with
identical pixel statistics, which is additional (not load-bearing) confirmation that
both dependency copies were equivalent.

## Checksums (clean rebuild, authoritative)
```
sha256  72ec8f64f811e6459e7a32e7a467f28491963607f6775149bd72a3a0291fcb2c  install/openmoonray/bin/moonray
sha256  c89ae49192adf77de10e0aabb418f5abf295bbce4d18119dee9789e0bfda8979  logs/phase03-rectangle.exr
```
(paths relative to `/root/moonray-blender/`, WSL-native)

## What was NOT committed and why
- `/root/moonray-blender/logs/phase03-build/*.log` — full build logs (up to ~260 KB
  each); excerpts are in `configure-summary.txt` above, full files remain WSL-native.
- `/root/moonray-blender/logs/phase03-rectangle.exr` — the render output itself (345 KB);
  its checksum, dimensions and pixel statistics are recorded in `render-check.txt`
  instead. Deliberately not committed: it is a transient build-verification artifact,
  not a repository asset, and 345 KB of binary EXR data has no diff/review value in git.
- Neither is large enough to strictly require exclusion, but neither adds verification
  value beyond what is already captured here in text form, so both are left out per the
  "avoid giant build logs/binaries in Git" instruction.
