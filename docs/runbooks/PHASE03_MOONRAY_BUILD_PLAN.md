# Phase 03 Build Plan — Native MoonRay Runtime (CPU baseline)

Status: EXECUTED 2026-09-09 — see `docs/completions/03-moonray-native-runtime.md` and
`docs/evidence/phase03/` for the actual result. **Sections 7 and 10 below describe the
originally prepared plan and were superseded by real execution evidence — see the
correction note immediately below before following them.**

## Correction after real execution (2026-09-09)

Inspecting the actual pinned `CMakeLists.txt` files (per this plan's own "Execution
strategy" mandate) before running the `--preset rocky9-release` configure in section 10
found that it would either hard-fail or silently drag in Hydra/hdMoonray/Arras/USD:
`openmoonray`'s top-level `CMakeLists.txt` and `moonray/CMakeLists.txt` call
`add_subdirectory()` **unconditionally** on `rats`, `arras/*`, `hydra`, `moonray_arras`,
`moonray_dcc_plugins`, `moonshine_usd` and `render_profile_viewer` — none of which this
project initializes, and several of which (`hydra` → `hdMoonray`, needs the full Pixar
USD stack) are explicitly out of scope per ADR-0002.

**What was actually run instead**: each required repository (`scene_rdl2`,
`mcrt_denoise`, `moonray`, `moonshine`) was configured and built **separately** against
its own `CMakeLists.txt`, per upstream's own documented alternative
(`building/general_build.md`, "Building the Repositories Separately") — see
`scripts/linux/phase03_build_moonray.sh`, `scripts/linux/phase03_build_deps.sh` and
`scripts/linux/phase03_install_packages.sh` for what was actually executed, and
`docs/evidence/phase03/README.md` for the full rationale. This is a build-*approach*
correction only — the pinned source commits in section 3 below are exactly what was
built; no source pin changed.

This is a plan only for sections other than 7/10 (superseded, see above). No command in
this document was run as part of *producing* it originally. See
`docs/research/03-upstream-pin-audit.md` for the pin reconciliation this plan builds on and
for build risks pulled from real upstream build files.

## Preconditions
- Phase 02 host verified (`docs/completions/02-host-runtime-foundation.md`).
- Phase 03 pre-build audit complete (`docs/research/03-upstream-pin-audit.md`).
- Explicit user approval to begin the actual build.

## 1. Clone/fetch strategy
```bash
wsl -d MoonRay-Rocky9
mkdir -p /root/moonray-blender/src
cd /root/moonray-blender/src
git lfs install
git clone https://github.com/OpenMoonRay/openmoonray.git
cd openmoonray
git checkout b9b0ac29135b26e20a51edf9028558bb64df6700
```
Clone first, then checkout the pinned commit explicitly, rather than
`--recurse-submodules` against a moving `main` — this guarantees the exact superproject
commit audited in `docs/research/03-upstream-pin-audit.md`, not whatever `main` has moved to
by build time.

## 2. Checkout strategy
After checking out the pinned superproject commit, submodules must be synced to the gitlinks
that commit's tree records (`configs/moonray-source-lock.json` for the CPU-baseline subset):
`cmake_modules`, `moonray/scene_rdl2`, `moonray/mcrt_denoise`, `moonray/moonray`,
`moonray/moonshine`. Do not `git submodule update --init --recursive` blindly for every
submodule if disk/time is constrained — the Hydra and Arras submodules
(`moonray/hydra/*`, `arras/*`, `moonray/moonshine_usd`) are excluded from the CPU baseline
per the audit and can be skipped by initializing only the required paths.

## 3. Submodule synchronization
```bash
git submodule update --init cmake_modules moonray/scene_rdl2 moonray/mcrt_denoise moonray/moonray moonray/moonshine
git -C moonray/scene_rdl2 rev-parse HEAD   # must equal 1229d3eaa1ee41dc1ddefbe781c623edceafbac8
git -C moonray/moonray rev-parse HEAD      # must equal eef67ae992b5037943a7716cca96ed443c36dcec
git -C moonray/moonshine rev-parse HEAD    # must equal a3c8667298a23df7d6efed128cb475484de66c8e
git -C moonray/mcrt_denoise rev-parse HEAD # must equal 0050e726309a533e7964bd05380430e6b06cce7a
git -C cmake_modules rev-parse HEAD        # must equal 1b1b7af8111b0a8ceaff45f3c47a778b0ca07ec4
```
Any mismatch here means the pin audit is out of date and must be redone before proceeding.

## 4. Linux-native source path
`/root/moonray-blender/src/openmoonray` — inside the WSL2 ext4 filesystem, never `/mnt/*`, per
the standing project constraint (Phase 02 evidence, NEXT_SESSION.md).

## 5. Build path
`/root/moonray-blender/build/openmoonray` (dependency build under
`/root/moonray-blender/build-deps`).

## 6. Install prefix
`/root/moonray-blender/install/openmoonray`.

## 7. CMake configuration
Rocky-9-specific flags are required per upstream's own build docs (see audit, build risk #2):
```bash
cmake --preset rocky9-release -DCMAKE_INSTALL_PREFIX=/root/moonray-blender/install/openmoonray \
  -DPYTHON_EXECUTABLE=python3 -DBOOST_PYTHON_COMPONENT_NAME=python39 -DABI_VERSION=0 \
  -DBUILD_QT_APPS=NO -DMOONRAY_USE_OPTIX=NO
```
Confirm `python3 --version` inside `MoonRay-Rocky9` actually reports 3.9.x before trusting
`BOOST_PYTHON_COMPONENT_NAME=python39` — this was not independently re-verified in the audit
(see build risk #2).

## 8. CPU-only baseline options
- `install_packages.sh --nocuda` (skip CUDA repo/package install).
- `-DMOONRAY_USE_OPTIX=NO` on the main configure (disables GPU/XPU code paths at build time).
- `-DBUILD_QT_APPS=NO` (skip `moonray_gui`/`arras_render`, avoids the Qt5 dependency entirely).
- Open question carried from the audit: whether `mcrt_denoise` needs an explicit flag of its
  own to fully disable its CUDA/OptiX/OpenImageDenoise GPU path, or whether
  `MOONRAY_USE_OPTIX=NO` alone is sufficient — resolve this during the actual configure step.

## 9. Dependency installation strategy
```bash
source building/Rocky9/install_packages.sh --nocuda
mkdir -p /root/moonray-blender/build-deps && cd /root/moonray-blender/build-deps
cmake /root/moonray-blender/src/openmoonray/building/Rocky9
cmake --build . -- -j 8   # start conservative, not -j $(nproc)=28, given 15 GiB WSL RAM (risk #5)
```

## 10. Build command
```bash
cd /root/moonray-blender/src/openmoonray
cmake --preset rocky9-release -B /root/moonray-blender/build/openmoonray \
  -DCMAKE_INSTALL_PREFIX=/root/moonray-blender/install/openmoonray \
  -DPYTHON_EXECUTABLE=python3 -DBOOST_PYTHON_COMPONENT_NAME=python39 -DABI_VERSION=0 \
  -DBUILD_QT_APPS=NO -DMOONRAY_USE_OPTIX=NO
cmake --build /root/moonray-blender/build/openmoonray -- -j 8
cmake --install /root/moonray-blender/build/openmoonray
```

## 11. Minimal standalone render test
```bash
source /root/moonray-blender/install/openmoonray/scripts/setup.sh
moonray -in /root/moonray-blender/src/openmoonray/moonray/moonray/testdata/rectangle.rdla \
        -out /root/moonray-blender/logs/phase03-rectangle.exr
```
(exact `testdata` path to be confirmed once the `moonray` submodule is actually checked out —
upstream's general build doc references `<source>/testdata/rectangle.rdla` relative to the
`moonray` repo root, not the `openmoonray` superproject root.)

## 12. Output artifact
`/root/moonray-blender/logs/phase03-rectangle.exr`, plus full build/install logs under
`/root/moonray-blender/logs/phase03-build/`.

## 13. Verification commands
```bash
file /root/moonray-blender/logs/phase03-rectangle.exr   # confirm valid EXR, non-zero size
ldd /root/moonray-blender/install/openmoonray/bin/moonray | grep -i "not found"  # must be empty
/root/moonray-blender/install/openmoonray/bin/moonray -help
```

## 14. Rollback / clean rebuild procedure
```bash
rm -rf /root/moonray-blender/build /root/moonray-blender/build-deps
# install/ is left in place unless the install itself is suspect; if so:
rm -rf /root/moonray-blender/install/openmoonray
```
Re-run from step 7 (dependencies in `build-deps` are cached by design; only steps 9-10 need to
re-run for a source-only rebuild). Re-cloning (`step 1`) is only needed if the pinned commit
itself is being changed, which requires re-running the Phase 03 pin audit first.

## Explicitly out of scope for this plan
Superseded: this plan (specifically sections 7 and 10) has been executed, with the
approach correction described at the top of this document. See
`docs/completions/03-moonray-native-runtime.md` and `docs/evidence/phase03/` for what
was actually run and observed.
