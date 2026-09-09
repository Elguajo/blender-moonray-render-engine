# Project Brief — Direct MoonRay Render Engine for Blender 5.2+

## Outcome
Create a production-oriented integration in which **MoonRay appears and behaves as a real Blender render engine** while the operator remains on a Windows 11 workstation. Blender and the renderer-facing native runtime execute in Linux under WSL2/WSLg.

The primary production path is a **direct Blender ↔ MoonRay bridge**, not Blender Hydra → hdMoonray. Hydra remains reference/fallback/benchmark only.

## Users and jobs
- Primary user: Blender-based 3D/motion/VFX artist on Windows 11.
- Core jobs:
  - select `MoonRay` from Blender's Render Engine menu;
  - use progressive MoonRay rendering in Rendered Viewport;
  - render F12/final frames and animation without manual external export per render;
  - receive Beauty/AOV output through Blender's Render Result/Compositor pipeline;
  - use predictable scene/material translation and understand known limits;
  - recreate the environment from pinned upstream sources.

## Must-have scope
- Windows 11 remains workstation host.
- WSL2/WSLg is the accepted Linux execution boundary.
- Blender 5.2.1 LTS Linux is the first pinned DCC baseline.
- MoonRay is built/installed reproducibly from pinned upstream sources.
- Blender integration uses `bpy.types.RenderEngine` (or the current supported Blender equivalent if API changes are verified later).
- Production baseline uses an out-of-process native `moonray_bridge` for crash/dependency isolation.
- Scene translation covers geometry, transforms, camera, core lights, instances and an explicitly supported material/texture subset.
- Progressive framebuffer/AOV transfer is efficient enough for the accepted viewport target; large buffers must not rely on per-pixel Python loops.
- Incremental updates are required for accepted interactive workflows.
- CPU rendering must pass before XPU/CUDA is accepted.
- Final release includes compatibility matrix, performance evidence, operator docs, known limitations and packaging/rollback path.

## Explicit constraints
- Do not implement a native Windows MoonRay port unless architecture is explicitly revisited.
- Do not replace MoonRay with another renderer.
- Do not treat Hydra/hdMoonray as the required primary production path after ADR-0002.
- Do not call Hydra slow without measured evidence; preserve it as a comparison/fallback experiment.
- Do not embed MoonRay libraries into Blender's process as the first production architecture; in-process integration requires later profiling + ABI/crash-risk justification.
- Do not accept batch-only RDL/USD export as the finished product.
- Do not run bulk production geometry/framebuffer transfer through Python element-by-element loops.
- Do not silently upgrade Blender, MoonRay or critical native dependencies after validation.
- After every phase: persist evidence/state, stop, and obtain explicit user approval before executing the next phase.

## Material assumptions
- WSL2/WSLg can host Blender GUI and native MoonRay processes on the target workstation.
- MoonRay's C++ `RenderContext` and scene_rdl2/RDL2 APIs are usable for a DCC bridge.
- CPU is an acceptable first rendering baseline.
- A native helper process plus IPC/shared-memory transport is acceptable user architecture if launch/management is automated and transparent from Blender.
- Dedicated Linux remains platform fallback if WSL2 later fails production acceptance.

## Ubiquitous Language
- **Direct Bridge** — Blender integration path that communicates directly with a MoonRay-native service/library without Hydra as mandatory scene/render transport.
- **Bridge Process** — crash-isolated native `moonray_bridge` process hosting scene_rdl2/MoonRay state.
- **Control Channel** — small commands/state updates between Blender and Bridge Process.
- **Bulk Transport** — efficient binary/shared-memory path for large geometry and framebuffer data.
- **Scene Translator** — deterministic mapping from Blender depsgraph data to MoonRay/RDL2 scene objects.
- **Incremental Update** — sending only affected scene state where technically valid instead of rebuilding/exporting the complete scene.
- **CPU Baseline** — mandatory first rendering success path independent of XPU/CUDA.
- **Production Acceptance** — Blender-native workflow validated for required features, stability, performance and repeatability with known limits documented.

## Out of scope — first release
- Native Windows MoonRay port.
- Rewriting MoonRay renderer internals.
- Full arbitrary Blender shader-node parity.
- Distributed Arras render farm.
- Blender versions older than 5.2.
- In-process integration solely for theoretical speed without measured bridge bottleneck.

## Success criteria
- Blender 5.2.1 Linux runs reliably through WSLg.
- MoonRay runtime is reproducible from pinned source/release identity.
- `MoonRay` appears as a selectable Blender Render Engine.
- Baseline scene renders through F12 with MoonRay and returns a correct Blender Render Result.
- Rendered Viewport displays progressive MoonRay output for accepted scene subset.
- Supported scene changes update predictably, with incremental-update performance measured.
- Required passes/AOVs enter Blender's pass/compositor workflow.
- Blender survives bridge-process failure and reports a useful recoverable error where feasible.
- Clean-environment installation and rollback are documented/repeatable.
- Final release includes source, specs, tests, evidence, benchmark methodology, operator guide and known limitations.

## Classification
- Planning depth: FULL
- Complexity: XL
- Risk: High
