# Phase 01 Research — Compatibility Matrix

Status: VERIFIED RESEARCH BASELINE
Date: 2026-09-08

## Decision summary

The selected production architecture is:

```text
Windows 11 host
└─ WSL2 + WSLg
   └─ Rocky Linux 9 target environment
      └─ Blender 5.2.1 LTS Linux (exact version pinned)
         └─ bpy.types.HydraRenderEngine (Hydra 2.0 host)
            └─ hdMoonray 10 (`dreamworksanimation/hdMoonray-fork`, branch `hdm_10`)
               └─ MoonRay 2026.29.1 baseline
```

CPU rendering is the first required rendering baseline. MoonRay XPU/CUDA is a separate validation gate and must not be assumed working merely because WSL2 exposes CUDA.

The existing community Blender integrations are reference material only, not trusted production engine glue as-is.

## Compatibility matrix

| Layer / option | Current evidence | Status for this project | Consequence |
| --- | --- | --- | --- |
| Windows 11 as workstation host | WSL2 and WSLg are supported on Windows 11; WSLg runs Linux GUI apps with vGPU-backed accelerated OpenGL | PASS | Keep Windows as user-facing workstation OS |
| MoonRay native Windows runtime | MoonRay upstream currently documents Linux and macOS builds; no native Windows build path is documented | FAIL | Do not target `blender.exe` + native MoonRay DLLs |
| Linux Blender inside WSL2 | WSL2 can run Linux GUI apps through WSLg | CONDITIONAL PASS | Selected host boundary; Phase 02 must verify Blender GUI, filesystem and GPU behavior on the actual workstation |
| Rocky Linux 9 | MoonRay upstream currently tests Rocky Linux 9 | PASS as MoonRay target distro | Prefer Rocky 9 for renderer compatibility; custom WSL distro/WSLg behavior still needs Phase 02 validation |
| Blender 5.2 LTS | Released 2026-07-14; current patch is 5.2.1 LTS from 2026-08-25; supported until July 2028 | PASS | Pin Blender 5.2.1 for the first validated stack; future 5.2.x updates require a compatibility rerun |
| Blender Hydra API | Blender 5.2 updated its implementation to Hydra 2.0; Blender states existing render delegates should continue through OpenUSD's abstraction | PASS at API level | Use Blender's official `bpy.types.HydraRenderEngine`, not a custom generic RenderEngine wrapper |
| Blender 5.2 OpenUSD | Blender 5.2 release source pins OpenUSD 26.03 | PASS / STRICT COUPLING | hdMoonray must be built for the USD actually loaded by Blender |
| Blender USD namespace | Blender's dependency build sets internal namespace `pxrBlender_v${USD_VERSION}`, therefore `pxrBlender_v26_03` for 5.2 | HIGH-RISK COUPLING | A vanilla USD 26.03 build is not automatically ABI-equivalent to Blender's bundled USD |
| hdMoonray as DCC Hydra delegate | MoonRay upstream states a DCC plugin must build/link against the DCC host's USD because incompatible USD versions can crash | REQUIRED | Treat Blender's USD build as the host SDK boundary |
| hdMoonray 10 | Announced 2026-08-28 on branch `hdm_10`; explicitly supports Hydra 2.0 clients; tested with USD 0.25.5, Houdini 21, Maya 2026, usdview/usdrecord | BEST CURRENT CANDIDATE | Prefer hdm_10 over older hdMoonray 7 for Blender 5.2 Hydra 2.0 |
| hdMoonray 10 with USD 26.03 | hdm_10 CMake rejects only PXR < 25.05; upstream testing is stated for 25.05, not 26.03 | UNKNOWN UNTIL BUILD/RUNTIME | Phase 03/04 must prove compile, plugin discovery and render stability against Blender's USD 26.03 build |
| MoonRay 2026.29.1 | Current upstream release on 2026-09-08; patch includes hdMoonray MaterialX Map shader changes | PASS as baseline release | Pin exact source revision in Phase 03; do not float to `main` |
| WSL2 CUDA | NVIDIA supports running/compiling Linux CUDA apps under WSL2 with the Windows NVIDIA driver | CONDITIONAL PASS | CUDA availability can be tested in Phase 02 |
| WSL2 OpenGL-CUDA interop | NVIDIA currently documents OpenGL-CUDA interop as unsupported, plus UVM/pinned-memory limitations | RISK / UNKNOWN FOR MOONRAY XPU | Do not make XPU a prerequisite for first MoonRay-in-Blender success; validate CPU first, then XPU separately |
| `cjhosken/mfb` | Repository README states “THIS ADDON IS CURRENTLY BROKEN” and supports Blender 4.1.0 | FAIL AS-IS | Reference only |
| `HorrorPills/MoonRay-Blender-Integration` | Repo claims Blender 4.x integration, but current engine code contains a placeholder generic RenderEngine path and imports `bl_hydra`; current Blender API uses `bpy.types.HydraRenderEngine` with `bl_delegate_id` and `pxr.Plug.Registry().RegisterPlugins` | FAIL AS-IS FOR 5.2 | Reference for UI/material ideas only; do not make it the production dependency |
| Separate USD batch render | hdMoonray 10 supports usdrecord-style batch usage | DIAGNOSTIC FALLBACK ONLY | Useful to isolate MoonRay/hdMoonray from Blender, but it does not satisfy the requested in-Blender Render Engine workflow |

## Critical ABI rule

The most important technical rule discovered in this phase is:

> **Do not build hdMoonray against an arbitrary system OpenUSD and then load it into Blender.**

Blender 5.2's build currently pins OpenUSD 26.03 and compiles it with a Blender-specific internal namespace. MoonRay's own DCC integration guidance says the Hydra delegate must build/link against the USD used by the host DCC because incompatible versions may crash.

Therefore the implementation strategy is:

1. pin exact Blender 5.2.1 source/build identity;
2. identify/reuse the matching Blender Linux dependency bundle or equivalent host USD headers/libraries/configuration;
3. build hdMoonray 10 against that host USD configuration, including Blender's internal namespace expectations;
4. only then register the plugin through Blender's official HydraRenderEngine path;
5. if the blender.org binary does not expose a workable SDK/ABI surface, build a pinned Blender 5.2.1 Linux host from source with its matching dependency bundle and build hdMoonray against the same dependency tree.

This controlled Blender build is the primary fallback. It is not a custom renderer implementation; it is an ABI-controlled host build.

## Render-engine API rule

For Blender 5.2 the engine adapter must follow the supported Blender API shape conceptually:

```python
class MoonRayHydraEngine(bpy.types.HydraRenderEngine):
    bl_idname = "..."
    bl_label = "MoonRay"
    bl_delegate_id = "<exact hdMoonray plugin id>"

    @classmethod
    def register(cls):
        bpy.utils.expose_bundled_modules()
        import pxr.Plug
        pxr.Plug.Registry().RegisterPlugins(["<plugin path>"])
```

This does **not** mean Phase 01 authorizes writing a new integration. The purpose is to define the compatibility contract used to evaluate existing glue and to keep Phase 04 on Blender's official Hydra API.

The exact hdMoonray plugin identifier must be obtained from the pinned hdm_10 build/plugin metadata during Phase 03/04 rather than guessed from older addons.

## Version policy

Initial frozen baseline:

- Windows: Windows 11, current supported build on the workstation.
- WSL: WSL2, updated before environment validation.
- Linux target: Rocky Linux 9.x, exact release recorded in Phase 02.
- Blender: **5.2.1 LTS**, released 2026-08-25.
- Blender OpenUSD baseline: **26.03**, with Blender internal namespace `pxrBlender_v26_03` per Blender 5.2 release source.
- hdMoonray: `dreamworksanimation/hdMoonray-fork`, branch `hdm_10`, exact commit to be frozen immediately before Phase 03 build.
- MoonRay: **2026.29.1**, exact release/tag/commit to be frozen in Phase 03.
- CUDA/OptiX: not frozen in Phase 01 because XPU is not the first acceptance target; versions must follow the pinned MoonRay build requirements and WSL driver constraints in Phase 02/03.

No component above may be silently auto-updated in the validated production environment.

## Architecture options evaluated

### A. Native Windows Blender + native MoonRay

Status: **REJECTED / FAIL under current upstream support**.

Reason: MoonRay documents Linux/macOS builds and no supported native Windows integration. A Linux `.so` in WSL cannot be loaded by Windows `blender.exe` as a Hydra delegate.

### B. Linux Blender inside WSL2/WSLg

Status: **SELECTED**.

Benefits:
- keeps Windows 11 as the workstation OS;
- places Blender, OpenUSD/Hydra, hdMoonray and MoonRay inside one Linux process/runtime boundary;
- WSLg preserves a desktop-like Linux Blender workflow;
- NVIDIA provides CUDA support to Linux applications in WSL2;
- aligns MoonRay with a Linux environment instead of inventing a Windows port.

Risks:
- custom Rocky Linux WSL/WSLg behavior needs real workstation validation;
- Blender's custom USD namespace/ABI is a nontrivial build coupling;
- hdMoonray 10 is newer than the currently merged OpenMoonRay mainline integration and is only explicitly tested upstream with USD 25.05;
- XPU may encounter WSL-specific CUDA limitations.

### C. Dedicated/remote Linux workstation

Status: **FALLBACK PLATFORM**, not primary.

Use only if WSL2/WSLg cannot provide stable GUI/GPU behavior or if MoonRay XPU relies on Linux capabilities unavailable under WSL2. The same pinned Blender/USD/hdMoonray architecture should be retained on bare-metal Linux.

## Primary fallback hierarchy

1. **Primary:** official Blender 5.2.1 Linux binary in WSL2 + matching host-USD-compatible hdMoonray build.
2. **ABI fallback:** pinned Blender 5.2.1 Linux built from source using Blender's matching precompiled dependency bundle; hdMoonray built against the exact same host dependency tree.
3. **Platform fallback:** move the same Linux stack to dedicated/bare-metal Linux while keeping Windows as the operator workstation if required.
4. **Diagnostic only:** usdrecord/standalone hdMoonray render to isolate renderer issues; this does not count as product acceptance.

## Phase 02 readiness criteria derived from research

Phase 02 may start when explicitly approved by the user. It must prove the host foundation before any MoonRay compilation:

- WSL2 health and version are recorded;
- Rocky Linux 9 environment starts reproducibly under WSL2;
- WSLg can launch a representative accelerated GUI application;
- Blender 5.2.1 Linux launches through WSLg;
- Blender reports expected version/platform and can save/read a test `.blend` in the chosen Linux project filesystem;
- Blender can import/use its bundled `pxr` modules sufficiently to inspect USD identity/namespace;
- Windows NVIDIA driver is visible through WSL where applicable;
- CUDA visibility is recorded as PASS/FAIL/NOT APPLICABLE without yet claiming MoonRay XPU compatibility;
- filesystem layout separates source, build, install, cache and production project data;
- no MoonRay/hdMoonray build is attempted until these checks pass.

## Primary sources

Accessed 2026-09-08.

1. Blender 5.2 LTS release/current patch:
   - https://www.blender.org/releases/5-2/
   - https://www.blender.org/download/lts/
   - https://download.blender.org/release/Blender5.2/
2. Blender 5.2 Hydra 2.0 API release note:
   - https://developer.blender.org/docs/release_notes/5.2/python_api/
3. Blender HydraRenderEngine API:
   - https://docs.blender.org/api/5.2/bpy.types.HydraRenderEngine.html
   - https://docs.blender.org/api/5.2/bpy.types.RenderEngine.html
4. Blender 5.2 dependency definitions (OpenUSD 26.03) and USD internal namespace setup:
   - https://github.com/blender/blender/blob/blender-v5.2-release/build_files/build_environment/cmake/versions.cmake
   - https://github.com/blender/blender/blob/blender-v5.2-release/build_files/build_environment/cmake/usd.cmake
5. MoonRay build support / Rocky 9:
   - https://docs.openmoonray.org/getting-started/installation/building-moonray/general_build/
   - https://docs.openmoonray.org/getting-started/installation/building-moonray/rocky9_build/
6. MoonRay current release:
   - https://github.com/OpenMoonRay/openmoonray/releases
7. MoonRay DCC plugin USD compatibility guidance:
   - https://github.com/OpenMoonRay/openmoonray/discussions/125
8. HdMoonray 10 announcement:
   - https://github.com/OpenMoonRay/openmoonray/discussions/270
   - https://github.com/dreamworksanimation/hdMoonray-fork/tree/hdm_10
9. Microsoft WSLg/Linux GUI documentation:
   - https://learn.microsoft.com/windows/wsl/tutorials/gui-apps
10. NVIDIA CUDA on WSL documentation:
   - https://docs.nvidia.com/cuda/wsl-user-guide/
11. Existing community integrations inspected:
   - https://github.com/cjhosken/mfb
   - https://github.com/HorrorPills/MoonRay-Blender-Integration

## Unresolved items intentionally deferred

- Whether Blender 5.2.1's shipped Linux package exposes all headers/libs/config needed to link hdm_10 directly, or whether a matching Blender source/dependency build is required.
- Exact hdm_10 commit and exact registered plugin identifier at implementation time.
- Whether hdm_10 builds and operates correctly against Blender's OpenUSD 26.03 namespace/ABI.
- Whether MoonRay XPU works reliably under WSL2 despite documented WSL CUDA limitations.
- Production behavior for MaterialX, AOVs, motion blur, DOF, volumes, hair, instancing and animation; these belong to later phases.

> **Historical note (2026-09-09):** ADR-0002 moved Hydra/hdMoonray from primary architecture to reference/fallback/benchmark. This matrix is retained as historical compatibility evidence.
