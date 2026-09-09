# Research — Phase 03 Upstream Pin Audit

Status: PRE-BUILD AUDIT COMPLETE — NO BUILD PERFORMED
Date: 2026-09-09

## Purpose

Prove that the exact upstream source revisions this project intends to build form one
internally consistent OpenMoonRay dependency set, **before** any Phase 03 build attempt.
This is preparation only: nothing was built, no dependency was installed, no Blender/MoonRay
code was written.

## Method

1. Read the previously recorded independent pins in `UPSTREAM_LOCK.json`.
2. Fetched the pinned `OpenMoonRay/openmoonray` superproject commit's real Git tree via the
   GitHub API (`gh api repos/OpenMoonRay/openmoonray/git/trees/<sha>`, recursing into
   `moonray/`, `arras/`, `moonray/hydra/`, `moonray/moonray_arras/`, `arras/distributed/`).
3. Read each submodule path's **gitlink** (`type: "commit"`) directly from that tree — this is
   the exact child commit the superproject actually references, not a separately fetched
   "latest" branch tip.
4. Compared every gitlink SHA against the previously recorded `UPSTREAM_LOCK.json` value.
5. Cross-checked the Blender pin against the official `blender/blender` GitHub mirror tag.
6. Read the real upstream build documentation (`openmoonray-docs` at the pinned docs commit,
   plus `openmoonray/building/Rocky9/*` at the pinned superproject commit) to determine the
   actual Rocky Linux 9 build/dependency requirements — not assumed from memory.

All SHAs below were fetched live from `api.github.com` on 2026-09-09 and are real, observed
values, not inferred or guessed.

## Authoritative superproject pin

```text
openmoonray: b9b0ac29135b26e20a51edf9028558bb64df6700  (2026-08-25T22:42:53Z)
```

This is the commit already recorded in `UPSTREAM_LOCK.json`. It was re-verified, not replaced:

- The commit exists and its tree is readable.
- As observed today, it is also the current tip of `openmoonray`'s `main` branch — i.e. the
  existing lock is not stale relative to upstream.
- A tagged release, `v2026.29.1` (`d96c6e30a8c280d4b5eb3bafa5e54efc445d7ea8`, published
  2026-07-17), exists and predates this pin by ~5.5 weeks. There is no concrete evidence
  (upstream issue, failed build report, regression) that the newer main-branch commit is
  less buildable than that release, so per the "do not silently move commits without a
  concrete reason" constraint, **main HEAD `b9b0ac2` is kept as the authoritative pin**. The
  tag is recorded below as a known rollback candidate only.

## Dependency reconciliation table

Gitlink column = the exact commit the `b9b0ac2` superproject tree points to for that path,
read directly from the Git tree API (not a separately fetched branch tip).

| Component | Repository | Existing lock (pre-audit) | Superproject gitlink | Final pin | Status |
|---|---|---|---|---|---|
| openmoonray | OpenMoonRay/openmoonray | `b9b0ac29135b26e20a51edf9028558bb64df6700` | n/a (anchor) | `b9b0ac29135b26e20a51edf9028558bb64df6700` | PASS — real commit, is current `main` tip |
| scene_rdl2 | OpenMoonRay/scene_rdl2 | `1229d3eaa1ee41dc1ddefbe781c623edceafbac8` | `1229d3eaa1ee41dc1ddefbe781c623edceafbac8` | `1229d3eaa1ee41dc1ddefbe781c623edceafbac8` | MATCH |
| moonray | OpenMoonRay/moonray | `eef67ae992b5037943a7716cca96ed443c36dcec` | `eef67ae992b5037943a7716cca96ed443c36dcec` | `eef67ae992b5037943a7716cca96ed443c36dcec` | MATCH |
| moonshine | OpenMoonRay/moonshine | `a3c8667298a23df7d6efed128cb475484de66c8e` | `a3c8667298a23df7d6efed128cb475484de66c8e` | `a3c8667298a23df7d6efed128cb475484de66c8e` | MATCH |
| mcrt_denoise | OpenMoonRay/mcrt_denoise | *not previously tracked* | `0050e726309a533e7964bd05380430e6b06cce7a` | `0050e726309a533e7964bd05380430e6b06cce7a` | ADDED — required internal dependency of `moonray` per upstream `repo_deps.md` |
| cmake_modules | OpenMoonRay/cmake_modules | *not previously tracked* | `1b1b7af8111b0a8ceaff45f3c47a778b0ca07ec4` | `1b1b7af8111b0a8ceaff45f3c47a778b0ca07ec4` | ADDED — shared CMake modules required by every component build |
| blender | blender/blender | `9e2066aef7ef7e20c142ad7bd3303138a4304c93` (source_tag v5.2.1) | n/a (unrelated project) | `9e2066aef7ef7e20c142ad7bd3303138a4304c93` | PASS — GitHub mirror tag `v5.2.1` resolves to exactly this SHA (independently re-verified this session, not just carried over from Phase 02) |
| docs (openmoonray-docs) | OpenMoonRay/openmoonray-docs | `74902f54fd490b3ec23b33505b99f37d44ef10e3` | n/a | `74902f54fd490b3ec23b33505b99f37d44ef10e3` | PASS, see documentation alignment below |

**Result: no mismatches.** The three previously-recorded MoonRay-family pins (`moonray`,
`scene_rdl2`, `moonshine`) already matched the superproject's own gitlinks exactly — they were
correctly reconciled when `UPSTREAM_LOCK.json` was first written, not independently fetched
"latest" snapshots as the raw lock file text alone would suggest to a future reader. Two
build-critical repositories the previous lock did not mention (`mcrt_denoise`, `cmake_modules`)
were identified and added.

## Full submodule inventory (all 20 gitlinks, observed)

`openmoonray` at `b9b0ac2` references 20 submodules (upstream prose says "19"; this is a minor
doc/reality drift, not a build risk). Every SHA below was read from the live tree, not guessed:

| Path | Gitlink SHA | Classification |
|---|---|---|
| `moonray/scene_rdl2` | `1229d3eaa1ee41dc1ddefbe781c623edceafbac8` | **Required — CPU baseline** |
| `moonray/mcrt_denoise` | `0050e726309a533e7964bd05380430e6b06cce7a` | **Required — CPU baseline** (moonray's internal dependency) |
| `moonray/moonray` | `eef67ae992b5037943a7716cca96ed443c36dcec` | **Required — CPU baseline** |
| `moonray/moonshine` | `a3c8667298a23df7d6efed128cb475484de66c8e` | **Required — CPU baseline** |
| `cmake_modules` | `1b1b7af8111b0a8ceaff45f3c47a778b0ca07ec4` | **Required — CPU baseline** (build tooling) |
| `moonray/moonray_gui` | `c16b83d304046442138486d278ea475365e6b72c` | Optional / later — Qt viewer, gated by `BUILD_QT_APPS` |
| `moonray/render_profile_viewer` | `b092e183a7194306a791008a8783c56c4487ed00` | Optional / later — perf tool |
| `moonray/moonray_dcc_plugins` | `5e19b0d8ef9afa37e7db437bde8e12960ff493b3` | Optional / later — no dependency on our headless bridge |
| `moonray/materialx_shaders` | `9b83c0051418e09869c14e2a86abe788a7ab7dca` | Optional / later — gated by `BUILD_MATERIALX_SHADERS` (default OFF) |
| `rats` | `f1278e08878edc6081ca119c03df5d34f0b4b4d5` | Optional / later — regression-test harness |
| `moonray/moonshine_usd` | `ee188dd2ce31906316e474dc033ba1274b045669` | **Hydra/USD-only — excluded** |
| `moonray/hydra/hdMoonray` | `986121dbb8817237c02a254d0c4470b5eb820f9e` | **Hydra-only — excluded** (ADR-0002) |
| `moonray/hydra/moonray_sdr_plugins` | `36a097e8d2796e138d0720a47b2ce79f89931af7` | **Hydra-only — excluded** (ADR-0002) |
| `arras/arras4_core` | `17c49f115dc9c849003cfa15aa05869c97c5d801` | **Excluded** — distributed rendering, not required by standalone `moonray`/`RenderContext` |
| `arras/arras_render` | `780ce9daac0e9e3271165a3c3707076b8b214099` | **Excluded** — distributed rendering |
| `arras/distributed/arras4_node` | `e5ccf1abe34d172203cc8febd027c850a1d9a843` | **Excluded** — distributed rendering |
| `arras/distributed/minicoord` | `0b9ad46536db0c0e2dfa632cd079807026fd9b8f` | **Excluded** — distributed rendering |
| `moonray/moonray_arras/mcrt_dataio` | `7d522815b566b215f6e48afd130a0fcb927efcfa` | **Excluded** — Arras-only progressive transport |
| `moonray/moonray_arras/mcrt_computation` | `ce2bd3d58d7fa0b09edc672333fa820a97020deb` | **Excluded** — Arras-only |
| `moonray/moonray_arras/mcrt_messages` | `fe95e9655a868eb0667c7ec1d2d6e9dcd53b1619` | **Excluded** — Arras-only |

Basis for the "Excluded — distributed rendering" classification: upstream's own
`repo_deps.md` lists `moonray`'s internal dependencies as `mcrt_denoise, scene_rdl2` only —
none of the `arras*`/`mcrt_dataio`/`mcrt_computation`/`mcrt_messages` family is a build
dependency of the `moonray` command-line renderer or its `RenderContext` API. They exist to
support DreamWorks' Arras distributed/farm rendering, which is out of scope for this project's
local single-machine CPU baseline and Direct Bridge architecture (ADR-0002).

## Documentation alignment

`docs/vendor/openmoonray/UPSTREAM.json` pins `openmoonray-docs` commit
`74902f54fd490b3ec23b33505b99f37d44ef10e3` (2026-08-27T17:59:55Z, "Update docs for 2026-08-27
internal release"). The pinned source snapshot (`b9b0ac2`) is dated 2026-08-25.

**Classification: newer than source, by 2 days.**

Implication: the vendored developer-reference documentation was published slightly *after*
the pinned source snapshot, as part of the same release window ("2026-08-27 internal
release"). It is not stale relative to the source; if anything it has a marginal informational
edge. No re-vendoring is warranted — the gap is two days against a project that documents
weekly/bi-weekly release cadence (`v2026.29.0`, `v2026.29.1`), and no content contradiction
was found between the vendored docs and the source pin during this audit.

## Build dependency graph (Phase 03 CPU baseline only)

```text
openmoonray superproject (b9b0ac2)
├── cmake_modules            [build tooling]
├── scene_rdl2               [MoonRay's scene representation]
├── mcrt_denoise             [denoiser; internal dep of moonray]
├── moonray                  [command-line renderer / RenderContext]
├── moonshine                [production shader set, incl. DwaBaseMaterial]
└── third-party (via building/Rocky9/install_packages.sh + build-deps CMake project):
    ├── OS packages (dnf/EPEL/CRB): boost 1.75, lua 5.4, openvdb 9.1, tbb 2020.3,
    │   log4cplus 2.0.5, cppunit 1.15.1, libmicrohttpd 0.9.72, gcc/g++, python3-devel
    └── built-from-source (building/Rocky9 ExternalProject_Add set): CMake ≥3.23.1,
        OpenImageIO 2.4.8, OpenEXR 3.1.8, OpenSubdiv 3.5.0, Embree 4.2.0, ISPC 1.21.0,
        Random123 1.14.0, JsonCpp, zlib
```

### Required for Phase 03 CPU baseline
`cmake_modules`, `scene_rdl2`, `mcrt_denoise`, `moonray`, `moonshine`, plus the third-party set
above. `moonshine` is required because the project's own `ARCHITECTURE.md` material-mapping
notes (scene_rdl2 Python bindings section) anticipate `DwaBaseMaterial` from `moonshine`, or
alternatively moonray-core's own `UsdPreviewSurface` — either way this audit does not resolve
that Phase 07 decision, it only confirms `moonshine`'s pin is internally consistent if chosen.

### Optional / later
`moonray_gui` (Qt viewer — useful for manual visual sanity checks but not required for a
scripted CPU render proof), `render_profile_viewer`, `rats` (regression suite), `materialx_shaders`.

### Hydra-only and therefore excluded
`hdMoonray`, `moonray_sdr_plugins`, `moonshine_usd` — all reference/fallback/benchmark under
ADR-0002, never part of the Direct Bridge production path.

### Excluded — distributed rendering (Arras), not XPU-related
`arras4_core`, `arras_render`, `arras4_node`, `minicoord`, `mcrt_dataio`, `mcrt_computation`,
`mcrt_messages`. Not required by `moonray`'s own dependency graph; this project targets a
single local `moonray_bridge` process, not DreamWorks' farm-distribution stack.

### XPU-only and therefore excluded from acceptance
GPU/XPU support (`MOONRAY_USE_OPTIX`, CUDA, OptiX headers, `mcrt_denoise`'s CUDA/OptiX/OIDN
GPU path) is build-time optional and excluded from Phase 03 acceptance per
`docs/project/PROJECT_BRIEF.md` ("CPU rendering must pass before XPU/CUDA is accepted").
Concretely this means passing `--nocuda` to `install_packages.sh` and
`-DMOONRAY_USE_OPTIX=NO` to the main CMake configure step (see build risks below).

## Build risks identified (from real upstream build files, not speculation)

All of the following are grounded in `openmoonray-docs` (`getting-started/installation/
building-moonray/{general_build,rocky9_build,repo_deps}.md`, pinned commit `74902f54f`) and
`openmoonray/building/Rocky9/{install_packages.sh,CMakeLists.txt}` at commit `b9b0ac2`:

1. **`install_packages.sh` installs CUDA by default.** Without passing `--nocuda`, the Rocky 9
   package script adds NVIDIA's CUDA repo and installs `cuda-runtime-11-8`/`cuda-toolkit-11-8`
   — this must be explicitly skipped for a CPU-only Phase 03 baseline, and
   `-DMOONRAY_USE_OPTIX=NO` must be set on the main `cmake` configure to fully disable GPU code
   paths at build time, not just skip package installation.
2. **CMake ≥3.23.1 is required**, mainly for ISPC integration; upstream's own script notes this
   is newer than most distro-provided CMake and downloads it directly from `github.com/
   Kitware/CMake` releases rather than via `dnf`. Rocky 9.8's own repos were not checked for a
   sufficient version in this audit; assume the manual download step is needed.
3. **ISPC 1.21.0** is a separate compiler toolchain (not a library), required by `moonray` and
   `moonshine` builds and located via the `ISPC` environment variable pointing at the compiler
   binary; not installed by the `dnf` package list — must come from the build-deps
   `ExternalProject_Add` step or a separate manual install.
2. **`ABI_VERSION=0` and `BOOST_PYTHON_COMPONENT_NAME=python39` are Rocky-9-specific required
   CMake flags** per upstream's own general build doc; using distro-default Python 3.9 boost
   bindings is load-bearing, and Rocky Linux 9.8 (Phase 02's verified baseline) ships Python
   3.9 as its default `python3`, which matches — but this must be re-confirmed against the
   actual `python3 --version` inside `MoonRay-Rocky9`, not assumed from the Rocky 9.8 label
   alone, since Blender's own bundled Python 3.13.13 (Phase 02 evidence) is unrelated and must
   not be confused with the system `python3` MoonRay's build expects.
3. **Git LFS is required before cloning.** Upstream's own instructions state some of the 20
   submodule repositories track files via Git LFS; `git lfs install` must run before
   `git clone --recurse-submodules`, or LFS-tracked files silently become pointer stubs.
4. **The dependency-build step is intentionally serial**, not parallel, per upstream's own
   `ExternalProject_Add` `DEPENDS` chain design (`building/Rocky9` CMake project) — expect this
   phase of the build to be slow even with `-j $(nproc)`, because parallelism only applies
   within each dependency's own build, not across dependencies.
5. **Memory/parallelism**: NEXT_SESSION already records WSL currently exposes 15 GiB RAM (of
   31.8 GiB host) and 28 vCPUs to `MoonRay-Rocky9`. Upstream gives no minimum RAM figure; a
   full `-j $(nproc)` parallel build of MoonRay + all third-party source dependencies on 28
   threads with 15 GiB RAM is a plausible OOM/swap risk that was not tested in this audit and
   should be watched (e.g. start with a lower `-j`, or raise `.wslconfig` memory, if the build
   stalls or the OOM killer fires).
6. **CRB (CodeReady Builder) repo must stay enabled** — already true per Phase 02 evidence
   ("CRB repository enabled") but is a real hard dependency of `install_packages.sh`
   (`dnf config-manager --enable crb`), not just a nice-to-have.
7. **`mcrt_denoise` pulls in `cppunit`/`cuda`/`openimagedenoise`/`optix`** per `repo_deps.md`;
   for the CPU baseline, its CUDA/OptiX inputs must resolve to "not present, GPU denoise
   disabled" rather than a hard configure failure — this specific flag combination was not
   found documented explicitly for `mcrt_denoise` alone (only the top-level
   `MOONRAY_USE_OPTIX` flag is documented) and is a genuine open question for the Phase 03
   build attempt itself, not resolved by this audit.
8. **Package availability on Rocky Linux 9.8 specifically** (vs. the Rocky 9.x the scripts were
   authored against) was not independently re-verified package-by-package in this audit; the
   scripts target Rocky Linux 9 generically and Phase 02 already confirmed CRB/EPEL work on
   9.8, but exact `dnf` package name/version availability (e.g. `openvdb-devel`,
   `tbb-devel`) can only be confirmed by actually running the script.

## Files changed by this audit

- `UPSTREAM_LOCK.json` — normalized schema, added `source`/`superproject_commit` provenance
  fields, added `mcrt_denoise` and `cmake_modules`.
- `configs/moonray-source-lock.json` — new minimal machine-readable build manifest.
- `docs/research/03-upstream-pin-audit.md` — this document.
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — new build plan, not executed.
- `docs/phases/03-moonray-native-runtime.md` — status normalized to reflect audit completion
  without claiming the phase itself is complete.
- `docs/project/NEXT_SESSION.md`, `AGENT_HANDOFF.md` — resume-state normalization.

## Explicitly not done

- No source was cloned or built.
- No dependency package was installed.
- No render was attempted.
- Phase 03 was not marked `[x]`; Phase 04 was not activated.
- No Phase 03 Completion Record was written.
