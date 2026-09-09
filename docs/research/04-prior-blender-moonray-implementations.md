# Research: Prior Public Attempts to Integrate MoonRay into Blender

Audit date: 2026-09-09. Method: `gh api`/`gh search` against live GitHub repository metadata, commit graphs,
compare diffs, and raw file contents (actual source inspected, not just READMEs). No repository was cloned,
built, installed, or executed. This is a research document; it does not change the approved Direct Bridge
architecture (ADR-0002) and does not start Phase 04.

Companion files: [`04-prior-implementation-matrix.json`](04-prior-implementation-matrix.json) (machine-readable),
[`PRIOR_ART.md`](PRIOR_ART.md) (quick index).

---

## Executive summary

Nine public repositories were audited: **3 published implementations** and **6 confirmed GitHub-tracked forks**.
A GitHub code/repo search for other MoonRay+Blender work (`hdMoonRay`, `MoonRayRenderEngine`,
`bl_idname MOONRAY`, `"moonray blender"`, etc.) found nothing beyond these nine.

Of the 3 published repositories, two (`cjhosken/mfb` and `cdnclass/moonray_for_blender`) are actually the
**same author's single continuous effort** — `cdnclass/moonray_for_blender` (2022, plain `RenderEngine`,
all callbacks stubbed) is an earlier, abandoned snapshot that shares initial commit history with the later,
more developed `cjhosken/mfb` (2022–2026, Hydra-based, still under intermittent development but explicitly
broken per its own README). The third, `HorrorPills/MoonRay-Blender-Integration`, is an unrelated single-session
scaffold (entire repo pushed within 53 seconds, template placeholders never edited, zero external engagement)
whose documentation substantially overstates non-functional code.

**All 6 known forks are zero-divergence stale mirrors** — every one shows `ahead_by: 0` against its parent on
GitHub's own compare API, several are byte-identical to each other. None contain independent work of any kind,
GPU-related or otherwise. They do not count as independent implementations.

**No project in this audit ever demonstrated MoonRay rendering a frame inside Blender**, via Hydra or any other
path. OpenMoonRay's own official repository (Discussion #211, Sept 2025) confirms this directly, referencing
`cjhosken/mfb`: RDLA export works, standalone `hd_render` works, but "rendering with hydra doesn't work" inside
Blender.

**No project ever proved GPU/XPU rendering.** The most GPU-aware repo (`cjhosken/mfb`) has a real, UI-wired
execution-mode dropdown offering an "XPU" option, but that value is never consumed by the render path, and the
project's own build script explicitly passes `-DMOONRAY_USE_OPTIX=NO`. The other two repos have, at best, an
unused enum or a single unimplemented "OptiX denoising" checkbox description string. No project contains
functional CUDA/OptiX code, a successful GPU build, or any benchmark data.

Separately, current upstream MoonRay documentation and the OpenMoonRay project's own community-reported
Discussions indicate that **OptiX/XPU is not currently functional under WSL2** (independent of GPU capability),
while CPU/vector-mode builds are reported working on WSL2. This directly supports — and does not contradict —
this project's existing Phase 03 decision to build MoonRay with `-DMOONRAY_USE_OPTIX=NO` as the CPU baseline.

None of the evidence gathered changes the Direct Bridge architecture decision (ADR-0002); if anything it
reinforces it, since the only prior project built directly on Blender's real Hydra API never got Hydra rendering
working in Blender at all.

---

## Project inventory

| Repository | Relationship | Author | Active | License | Status |
|---|---|---|---|---|---|
| [`cjhosken/mfb`](https://github.com/cjhosken/mfb) | original | Christopher Hosken | 2022-08-14 → 2026-07-16 | GPL-3.0 | broken (author's own words) |
| [`cdnclass/moonray_for_blender`](https://github.com/cdnclass/moonray_for_blender) | original (same author/lineage as above) | Christopher Hosken | 2022-08-14 → 2022-08-21 | GPL-3.0 | abandoned prototype, all render callbacks are `pass` |
| [`HorrorPills/MoonRay-Blender-Integration`](https://github.com/HorrorPills/MoonRay-Blender-Integration) | original | HorrorPills | 2026-02-09 (53-second single session) | none (README claims Apache-2.0; no LICENSE file exists) | prototype, non-functional, docs overstate implementation |
| [`mnraker/moonray_2_blender`](https://github.com/mnraker/moonray_2_blender) | fork of `cjhosken/mfb` | — | fork event only, 0 unique commits | GPL-3.0 (inherited) | stale mirror |
| [`SacredCodeWriter/MoonRay-Blender-Addon`](https://github.com/SacredCodeWriter/MoonRay-Blender-Addon) | fork of `cjhosken/mfb` | — | fork event only, 0 unique commits | GPL-3.0 (inherited) | stale mirror (identical to `fantomid/mfb`) |
| [`fantomid/mfb`](https://github.com/fantomid/mfb) | fork of `cjhosken/mfb` | — | fork event only, 0 unique commits | GPL-3.0 (inherited) | stale mirror (identical to `SacredCodeWriter/MoonRay-Blender-Addon`) |
| [`Dinesh0N/Moonray-for-Blender`](https://github.com/Dinesh0N/Moonray-for-Blender) | fork of `cjhosken/mfb` | — | fork event only, 0 unique commits | GPL-3.0 (inherited) | stale mirror |
| [`mnraker/moonray_for_blender`](https://github.com/mnraker/moonray_for_blender) | fork of `cdnclass/moonray_for_blender` | — | fork event only, 0 unique commits | GPL-3.0 (inherited) | byte-identical mirror (identical to `SakuraEntropia/moonray_for_blender`) |
| [`SakuraEntropia/moonray_for_blender`](https://github.com/SakuraEntropia/moonray_for_blender) | fork of `cdnclass/moonray_for_blender` | — | fork event only, 0 unique commits | GPL-3.0 (inherited) | byte-identical mirror (identical to `mnraker/moonray_for_blender`) |

No repository claims or shows Windows-native support; `cjhosken/mfb` and `HorrorPills/...` target Linux
(and macOS for the latter); WSL2/native-Linux is the only realistic host for any of them, matching this
project's own architecture.

---

## Fork genealogy

```text
cjhosken/mfb  (Christopher Hosken, Hydra-based, active-but-broken through 2026-07-16)
├── mnraker/moonray_2_blender            frozen @ 979c2f1 (2024-08-06), 60 commits behind current HEAD, 0 ahead
├── SacredCodeWriter/MoonRay-Blender-Addon  frozen @ 144b9e0 (2025-05-25), 2 behind, 0 ahead
├── fantomid/mfb                         frozen @ 144b9e0 (2025-05-25), 2 behind, 0 ahead  [identical HEAD to SacredCodeWriter's fork]
└── Dinesh0N/Moonray-for-Blender         frozen @ da737bb (2025-05-17), 5 behind, 0 ahead

cdnclass/moonray_for_blender  (same author, earlier abandoned snapshot, dormant since 2022-08-21;
                                shares initial-commit history with cjhosken/mfb but is not GitHub-tracked as its fork)
├── mnraker/moonray_for_blender          identical @ c9aaf70, 0 ahead / 0 behind
└── SakuraEntropia/moonray_for_blender   identical @ c9aaf70, 0 ahead / 0 behind  [identical HEAD to mnraker's fork]

HorrorPills/MoonRay-Blender-Integration  (unrelated single-session scaffold; 0 forks)
```

Every fork shows `ahead_by: 0` against its parent via GitHub's compare API — **zero unique commits, in every
case**. No fork contains a bug fix, feature, or GPU-related change not already present in its parent. None of
the six forks have downstream forks of their own. Practically: this audit found **2 real authorial lineages**
(Christopher Hosken's `cdnclass` → `cjhosken/mfb` continuum, and HorrorPills' standalone scaffold), not 9.

---

## Architecture comparison

| Repository | Claimed architecture | Actual architecture (from source) |
|---|---|---|
| `cjhosken/mfb` | Hydra-based | **B. Hydra-based**, genuinely built on `bpy.types.HydraRenderEngine` with `bl_delegate_id = "HdMoonrayRendererPlugin"`. Real registration/plugin-path wiring. No render-loop override — relies entirely on Blender's built-in Hydra loop, which per official upstream evidence does not actually render MoonRay content (see below). |
| `cdnclass/moonray_for_blender` | (unstated) | **D. UI/prototype only.** Plain `bpy.types.RenderEngine`; `render()`, `view_update()`, `view_draw()` are all literally `pass`. |
| `HorrorPills/MoonRay-Blender-Integration` | B. Hydra-based (per README) | **D. UI/prototype only**, despite the claim. A `HydraRenderEngine` subclass exists in source but is gated behind `import bl_hydra` — a module that does not exist in real Blender (the actual API imports `HydraRenderEngine` from `bpy.types`). This import always fails, so the Hydra engine class can never register; only a do-nothing placeholder `RenderEngine` is ever active. |

None of the three audited repositories implement or attempt **A. Direct MoonRay integration** (custom
bridge/binding → scene_rdl2 → RenderContext, in-process or via IPC) — the architecture this project has adopted
per ADR-0002. This project's Direct Bridge approach has no prior public precedent to draw code from, for better
or worse; it also means none of this audit's negative findings about the Hydra path (see next section)
automatically apply to the Direct Bridge design.

---

## Feature implementation matrix

Full per-project detail (with file/line citations) is in the individual agent findings folded into this
document's project sections below and in the JSON matrix. Summary (strict grading — a `pass`-only function
body is `PLACEHOLDER`, not `IMPLEMENTED`):

| Capability | `cjhosken/mfb` | `cdnclass/moonray_for_blender` | `HorrorPills/...` |
|---|---|---|---|
| RenderEngine / HydraRenderEngine subclass | IMPLEMENTED (Hydra) | IMPLEMENTED (plain) | PLACEHOLDER (Hydra class unreachable) |
| F12 final render | PARTIAL (delegated to Blender's Hydra loop, unverified) | PLACEHOLDER (`pass`) | PLACEHOLDER (empty buffer) |
| Viewport / progressive rendering | PARTIAL / UNKNOWN | PLACEHOLDER (`pass`) | PLACEHOLDER (`pass`) |
| Scene export (RDL/RDLA/RDLB) | IMPLEMENTED (secondary path via USD→`hd_usd2rdl`) | NOT FOUND | NOT FOUND |
| USD export | IMPLEMENTED (intermediate step) | NOT FOUND | PLACEHOLDER (hand-built dict, not real `pxr.Usd`) |
| Materials (Principled→DwaBase) | PARTIAL (node scaffolding, no conversion logic found) | PARTIAL (scaffolding only) | PARTIAL (real traversal logic exists, but never called from the render path) |
| AOVs / Cryptomatte | IMPLEMENTED (settings surface only) | NOT FOUND | NOT FOUND |
| Settings UI | IMPLEMENTED (~100+ SceneVariables keys) | PARTIAL (7 panels, no consumer) | IMPLEMENTED (5 panels, no consumer) |
| Packaging / build automation | IMPLEMENTED (857-line `build.py`, but build currently fails) | NOT FOUND | PARTIAL (plausible scripts, never observed to succeed) |
| Crash recovery, motion blur, instances, animation, EXR | NOT FOUND / UNKNOWN across all three | | |

**The single most substantive piece of code found in this entire audit** is `HorrorPills/...`'s
`material_conversion/converter.py` (real Principled-BSDF → DwaBase graph traversal with Blender 3.x/4.x
socket-name handling) — but it is dead code, never invoked by that repo's own render path, and its license is
unresolved (see Code/licensing considerations).

---

## NVIDIA GPU / XPU matrix

Distinguishing UI presence, code presence, dependency config, and proof of an actual build/render/benchmark —
per the audit's required six-tier scale:

| Repository | GPU UI option | GPU code | GPU dep. config | GPU build succeeded | GPU render succeeded | Benchmark measured |
|---|---|---|---|---|---|---|
| `cjhosken/mfb` | **Yes** — real `execution_mode` enum (Scalar/Vector/XPU/Auto), drawn in the Render properties header, description text copied from upstream MoonRay docs | No (the enum value is never read by `get_render_settings()` — disconnected from the render path) | **Explicitly disabled** — `build.py` passes `-DMOONRAY_USE_OPTIX=NO` | No | No | No |
| `cdnclass/moonray_for_blender` | Nominally yes, but **dead code** — a 2-item CPU/GPU enum in `preferences.py` never drawn in any panel | No | No (no build scripts exist in this repo) | No | No | No |
| `HorrorPills/MoonRay-Blender-Integration` | No dedicated toggle (`bl_use_gpu_context = False`, explicit); one `use_denoising` checkbox labeled "Enable OptiX denoising (if available)", wired to a UI panel but never read by `render()` | No | No | No | No | No |

`bl_use_gpu_context = True/False`, seen set in two of the three repos, is a Blender viewport-OpenGL-context-access
flag unrelated to MoonRay's own CUDA/OptiX compute backend — per this audit's methodology it is explicitly **not**
counted as GPU-rendering evidence in the table above.

**No repository in this audit contains functional CUDA/OptiX code, a GPU build that is known to have succeeded,
a GPU render that is known to have happened, or any performance measurement.** All forks inherit their parent's
GPU state unchanged (0 unique commits each).

---

## MoonRay upstream GPU/XPU facts (current official sources, 2026-09-09)

1. **CPU vs. XPU.** MoonRay's `-exec_mode` flag selects `scalar`, `vector` (SIMD CPU), `xpu`, or `auto`. XPU is
   *vector mode with occlusion-ray processing offloaded to GPU* — not a standalone GPU path tracer. Per
   OpenMoonRay's own Sept-2024 SIGGRAPH BoF Discussion post, extending GPU offload to direct/indirect rays was
   still in progress at that time; no newer official status update was found (neither `moonray` nor `openmoonray`
   has a `CHANGELOG.md`).
2. **NVIDIA GPU code** lives entirely in `moonray/lib/rendering/rt/gpu/optix/` (`OptixGPUAccelerator.cc/h`,
   `OptixGPUPrograms.cu`, etc.) — not in `scene_rdl2` or `hdMoonray`, both of which have zero GPU-related code.
   There is no plain-CUDA-without-OptiX path; the `.cu` kernel is compiled and run through the OptiX pipeline.
   A separate Metal path exists for Apple Silicon, unrelated to NVIDIA.
3. **Build flags:** `MOONRAY_USE_OPTIX` is the current authoritative CMake flag (gates both the CUDA toolkit and
   OptiX SDK requirement); `MOONRAY_USE_CUDA` appears only in older (2023) community posts and is not present
   in the current `main` `CMakeLists.txt` — treat it as a superseded name. `MOONRAY_USE_METAL` is the separate
   Apple flag.
4. **Pinned versions:** CUDA Toolkit **11.8** (official Rocky 9 install script) and OptiX **7.6 exactly** — official
   docs state explicitly that MoonRay is not yet compatible with newer OptiX releases.
5. **Minimum GPU architecture / driver version: UNKNOWN.** No official doc states one, and no compute-capability
   or architecture-name check exists anywhere in the GPU accelerator code or `FindOptiX.cmake`.
6. **Maturity language:** no official source calls XPU "production-ready" or "research-only" verbatim. The most
   specific official statement (`GPUAccelerator.h` design doc + the Sept-2024 Discussion post) describes it as
   shipped but partial — occlusion-ray GPU offload only, with further ray-type coverage explicitly future work
   at that time.
7. **Feature parity:** not full parity. XPU inherits vector mode's own gaps versus scalar mode (no
   physically-correct overlapping dielectrics, no variance buffers, no volume+deep combination) plus XPU-specific
   gaps (round bezier curves; round curves/meshes with more than 2 motion samples). Official docs describe an
   automatic, silent fallback from XPU to CPU vector mode on insufficient GPU memory or GPU-init failure.
8. **WSL2:** CPU/vector-mode builds are reported working on WSL2 in OpenMoonRay's own official Discussions
   (#90 Apr 2023, #183 Feb 2025, #211 Sept 2025 — the last including a live "MoonRay on WSL" demo on a
   pre-Ampere 2015 laptop, i.e. CPU/vector mode, not XPU). **OptiX/XPU is explicitly reported non-functional
   on WSL2** in the same official Discussions thread (#90), citing NVIDIA's own developer-forum reports of
   `libnvoptix_loader.so.1` failures and an NVIDIA OptiX engineer's 2022 statement that WSL2 OptiX support was
   still months away at minimum. No later official-repo evidence (through Sept 2025) contradicts this. No
   official DreamWorks/OpenMoonRay statement declares WSL2 officially supported for either mode.
9. **RTX 3060 assessment:** the card's own architecture (Ampere, compute capability 8.6) is well above the
   documented Pascal-and-later floor for CUDA-on-WSL2 in NVIDIA's own docs, and would very likely satisfy
   MoonRay's requirements **on native Linux**. On **WSL2 specifically**, current evidence points to OptiX/XPU
   not being currently workable — the blocker is the WSL2 OptiX runtime itself, not the RTX 3060's capability.
10. **Blender + Hydra + MoonRay, official status:** OpenMoonRay's own Discussion #211 (Sept 2025), referencing
    `cjhosken/mfb` directly, states: RDLA export works, standalone `hd_render` works, but *"rendering with hydra
    doesn't work"* inside Blender — the most current and most specific official statement available, and it
    matches this audit's independent code-level finding that no repository ever achieved a working Blender
    render path.
11. **AMD `BlenderUSDHydraAddon`** (reference comparison only): a mature, actively shipped Hydra-based Blender
    render engine addon with real GPU rendering via Radeon ProRender (vendor-agnostic Vulkan/HIP-backed compute,
    not tied to one vendor's proprietary API the way MoonRay's OptiX-only NVIDIA path is). It demonstrates that
    a working GPU-accelerated Hydra render engine inside Blender is achievable in principle — MoonRay's own
    Hydra-Blender integration has simply not reached that point yet, per official upstream statements.

---

## What actually rendered

**Nothing.** No audited repository, fork, or the official upstream integration path has been shown — by its own
authors, by official OpenMoonRay statements, or by this audit's code inspection — to render a MoonRay frame
inside Blender, on CPU or GPU. The closest any project got:
- `cjhosken/mfb`: RDL/RDLA export to disk works as a *secondary* operator (invoking external `hd_usd2rdl`/`maketx`);
  the actual in-Blender Hydra render path was never confirmed working, and per official upstream evidence,
  currently does not work.
- Standalone `hd_render`/`moonray_gui` (outside Blender entirely) is confirmed working by official upstream
  sources — this is MoonRay working as a renderer, not evidence of any Blender integration.

## What was only placeholder/prototype

- `cdnclass/moonray_for_blender`: every render-path method (`render`, `view_update`, `view_draw`) is a literal
  `pass`.
- `HorrorPills/MoonRay-Blender-Integration`: `HydraRenderEngine` subclass is unreachable dead code (nonexistent
  `bl_hydra` import); `render()` writes no pixels; `export_to_usd_material()` fabricates a dict rather than
  calling real USD APIs; extensive README/PROJECT_OVERVIEW "✅ Implemented" claims do not match the code.
- All 6 forks: verbatim, unmodified snapshots of their parent — no independent work exists to classify.

---

## Known failure modes

1. **Blender↔Hydra↔hdMoonray integration itself does not work yet**, per the one project that genuinely
   attempted it and per OpenMoonRay's own official confirmation. This is an upstream/ecosystem-level gap, not
   a single project's bug.
2. **OptiX 7.6 pin is fragile** — MoonRay explicitly does not support newer OptiX releases, which constrains any
   future GPU work to an old, specific SDK version.
3. **OptiX under WSL2 is reported non-functional** by both NVIDIA's own developer-forum threads and OpenMoonRay's
   community discussions, with no confirmed fix as of Sept 2025.
4. **USD/NDR header breakage**: `cjhosken/mfb`'s only open issue is exactly this — "Blender OpenUSD missing NDR"
   — matching a workaround already present in its own `build.py` (`install_ndr_headers()`), for NDR headers
   removed in USD 26.x but still required by OpenMoonRay. Relevant if this project's Blender/USD version ever
   needs NDR headers for any purpose.
5. **Documentation-vs-code mismatch is a recurring pattern** (2 of 3 repos): `HorrorPills/...`'s README claims
   substantially exceed its code; `cjhosken/mfb`'s README/`bl_info` disagree on supported Blender version.
   Evaluate any future third-party MoonRay-Blender code claims by reading the source, not the README.
6. **GitHub "Fork" activity is not a signal of ecosystem health** — 6 forks exist, all are inert mirrors; fork
   count should not be read as adoption or validation.

---

## Reusable components

Nothing is recommended for direct import (see licensing section). As **design reference only**:

| Source | What it shows | License | Caveat |
|---|---|---|---|
| `cjhosken/mfb`, `props/__init__.py` / `nodes/*.py` | Fairly complete enumeration of MoonRay `SceneVariables` mapped to Blender `PropertyGroup`s — useful as a settings-coverage checklist | GPL-3.0 | Shaped for Hydra's `get_render_settings()` dict, not a Direct Bridge's IPC schema; re-derive rather than port |
| `cjhosken/mfb`, `operators/io.py` | Pattern for invoking external `hd_usd2rdl`/`maketx` tools from a Blender operator | GPL-3.0 | Secondary/export path, not primary render path; the Direct Bridge will not go through USD at all |
| `cjhosken/mfb`, `build.py` | Pinned-dependency build orchestration pattern (SHA-pinned submodules, header-workaround pattern for the NDR/USD-26.x issue) | GPL-3.0 | Linux/`apt`-specific; not portable to this project's WSL2/Rocky 9 + Windows-host toolchain as-is, but the *pattern* (and the NDR workaround specifically) is worth knowing about |
| `HorrorPills/...`, `material_conversion/converter.py` | Genuine Principled-BSDF → DwaBase traversal logic with Blender 3.x/4.x socket-name compatibility handling | **Unresolved — README claims Apache-2.0 but no LICENSE file exists in the repo** | Do not reuse literally until license is resolved (contact author or find a LICENSE commit); the *approach* (walk from Principled BSDF, handle per-Blender-version socket renames) is useful to know about regardless |

## Code/licensing considerations

This repository is **GPL-3.0-or-later**. `cjhosken/mfb` and `cdnclass/moonray_for_blender` (and their forks)
are GPL-3.0, which is license-compatible for reuse with attribution if literal code is ever imported (a separate,
explicit future task per the assignment's constraints — not done here). `HorrorPills/MoonRay-Blender-Integration`
has **no LICENSE file despite a README claim of Apache-2.0** — GitHub's own license detector returns null, and
the README claim cannot be relied on. Treat this repository's code as all-rights-reserved until either a LICENSE
file appears or the author confirms terms directly; this is a stricter problem than ordinary GPL-compatibility
and should block any reuse of its (otherwise interesting) material-conversion logic until resolved.

---

## Lessons for our Direct Bridge

- **What validates the direction:** No prior project attempted architecture A (Direct Bridge: custom
  binding → scene_rdl2 → RenderContext). The one project that built on Blender's real Hydra API (architecture B)
  never got it rendering, and OpenMoonRay's own team confirms Blender↔Hydra integration doesn't work yet. This is
  circumstantial support for bypassing Hydra rather than depending on it — the Direct Bridge does not inherit
  whatever is currently broken in Blender's Hydra/hdMoonray path, because it does not use that path at all.
- **What prior failures this design avoids:** dependency on `bpy.types.HydraRenderEngine` + `hdMoonray` plugin
  registration (currently non-functional per upstream); dependency on a fictitious/incorrect Blender API surface
  (`HorrorPills/...`'s `bl_hydra` mistake); documentation-driven development without verifying against actual
  Blender/MoonRay APIs.
- **Problems that remain regardless of Hydra vs. Direct Bridge:** the OptiX-7.6-exact pin and its narrow
  compatibility window; the USD/NDR header breakage pattern if USD is touched for any reason; MoonRay's own XPU
  feature gaps (curves, motion samples, volumes) that any renderer-settings UI needs to expose or restrict
  correctly regardless of integration architecture.
- **Problems specific to Blender:** none of the audited projects solved progressive viewport rendering,
  cancellation, or crash recovery — all were NOT FOUND or PLACEHOLDER across every repo. These remain fully
  open problems for Phase 08 (interactive viewport) and Phase 11 (stability), with zero prior art to draw on.
- **Problems specific to MoonRay:** the OptiX 7.6 pin; the documented CPU/XPU feature-gap list; the unresolved
  minimum-GPU-architecture/driver-version questions (upstream doesn't document them — this project would need
  to establish its own empirical floor if it ever pursues XPU).
- **Problems specific to GPU/XPU:** WSL2 OptiX non-functionality is the dominant, well-evidenced risk — independent
  of which Blender-integration architecture is used, XPU rendering is not expected to work in this project's
  current WSL2 host environment without either a native-Linux host, a Windows-native MoonRay/OptiX build (not
  known to exist), or an upstream/NVIDIA fix to WSL2 OptiX support that isn't currently evidenced.

**No evidence found in this audit requires changing the Direct Bridge architecture decision.**

---

## GPU-specific risks for RTX 3060 / WSL2

1. **OptiX/XPU is very likely non-functional in the current WSL2 host**, independent of the RTX 3060's own
   adequacy — this is a platform-runtime risk, not a hardware risk. Any Phase 03+ GPU/XPU acceptance gate must
   treat this as the primary open question, not "does the card meet spec."
2. **No official minimum GPU architecture/driver is documented**, so even after clearing the WSL2/OptiX question,
   this project would need to establish empirically (via its own Phase 03+/XPU-specific validation) whether the
   installed driver and RTX 3060 combination actually initializes MoonRay's OptiX accelerator, rather than relying
   on any official compatibility table (none exists).
3. **OptiX SDK version is pinned to exactly 7.6** — a future GPU build must source that exact SDK version;
   using a newer OptiX release is explicitly documented as unsupported by MoonRay upstream.
4. **XPU has real feature gaps vs. CPU** (curves, motion-sample counts, volumes) with silent fallback to CPU on
   unsupported scenes/insufficient memory — any future XPU acceptance test must include scenes that exercise
   these gaps deliberately, or risk silently validating CPU fallback behavior while believing GPU is being tested.
5. **This project must not claim MoonRay XPU works on this machine** without a dedicated, explicit GPU/XPU
   validation phase — nothing in this audit, upstream docs, or Phase 02 evidence constitutes that proof. Phase 02
   evidence (`nvidia-smi` works, CUDA/OptiX *user-mode libraries visible*) demonstrates driver/library presence
   only, not a working OptiX runtime path, and is explicitly insufficient to claim GPU rendering capability.

## What a later GPU-specific validation phase must prove

To move past "unknown" on XPU for this workstation, a dedicated future phase (not this one, not Phase 03) would
need to independently demonstrate, in order:
1. An OptiX 7.6-enabled MoonRay build actually compiles inside `MoonRay-Rocky9` (`-DMOONRAY_USE_OPTIX=YES`, with
   CUDA Toolkit 11.8 and OptiX SDK 7.6 present).
2. The resulting binary successfully initializes the GPU accelerator at runtime inside WSL2 (not just that the
   binary links) — this is exactly the step multiple community reports say fails on WSL2.
3. A minimal scene renders via `-exec_mode xpu` and produces correct (or at least non-fallback, GPU-attributable)
   output — distinguishing a genuine XPU render from a silent fallback to CPU vector mode.
4. Optionally, a performance comparison against the CPU vector-mode baseline, only after step 3 is proven.
Steps 1–3 are all currently unproven for this project and unproven anywhere in the public record for WSL2.

---

## Recommendations

1. **Do not depend on any prior repository's code for the Direct Bridge's core render path** — no prior project
   implements architecture A, and the closest analog (Hydra path) is confirmed non-functional upstream.
2. **Treat `cjhosken/mfb`'s SceneVariables/property coverage as a checklist reference only** when Phase 06/07
   design the MoonRay settings UI — re-derive against current `scene_rdl2` SceneVariables rather than porting
   Hydra-shaped code.
3. **Resolve `HorrorPills/...`'s licensing question before considering its material-conversion approach** even
   as inspiration for Phase 07 (materials/textures) — currently legally unresolved (no LICENSE file despite an
   Apache-2.0 README claim).
4. **Keep XPU/GPU support formally out of scope** until a dedicated validation phase (see above) proves the three
   ordered steps on this workstation — the current CPU-only Phase 03 baseline is the only evidenced-safe path
   forward, consistent with the existing "CPU is mandatory first render baseline; XPU/CUDA is a separate evidence
   gate" decision in `docs/project/NEXT_SESSION.md`.
5. **When Phase 03+ eventually revisits GPU**, budget for OptiX SDK 7.6 specifically (not "latest OptiX") and for
   the real possibility that WSL2 blocks OptiX entirely regardless of driver/toolkit versions — a native-Linux
   or dual-boot fallback plan may be worth scoping *if and when* GPU/XPU becomes a project requirement, but that
   decision is out of scope for this research task.
6. **Do not import any third-party source code as a result of this audit** — per the assignment's constraints,
   this is a research-only deliverable; actual reuse (even of the GPL-3.0 `cjhosken/mfb` material) is a distinct,
   explicit future task requiring its own approval.
