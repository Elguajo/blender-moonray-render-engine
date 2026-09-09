# ADR-0002 — Direct MoonRay Bridge is the primary Blender integration

Status: ACCEPTED
Date: 2026-09-09
Supersedes: renderer-integration portion of ADR-0001 / Phase 01 architecture

## Context
The project goal is a Blender-native MoonRay Render Engine with Rendered Viewport, F12, animation and AOV output. A Hydra/hdMoonray path is viable as a standards-based integration, but it introduces an additional scene/renderer abstraction and a host-USD compatibility boundary. The user explicitly prefers a direct integration and wants Hydra retained only if useful as fallback/reference.

MoonRay exposes native renderer APIs including a top-level `RenderContext`, frame lifecycle control, scene updates between renders, progressive render-buffer snapshots and AOV snapshots. Blender exposes a RenderEngine lifecycle suitable for custom renderer integration.

No evidence currently proves that Hydra is slower in this exact Blender/MoonRay configuration. Performance must be benchmarked rather than assumed.

## Decision
Build a **Direct Blender ↔ MoonRay Bridge** as the primary product architecture.

Initial production boundary:
1. Blender add-on owns DCC UI, depsgraph observation, RenderEngine/F12/viewport/pass integration.
2. A separate native `moonray_bridge` process owns MoonRay and scene_rdl2 dependencies.
3. Small lifecycle/settings/status updates use local IPC.
4. Large geometry/framebuffer/AOV payloads use an efficient binary/shared-memory strategy selected and benchmarked during implementation.
5. Hydra/hdMoonray moves to `experiments/hydra/` as fallback/reference/benchmark and is not required for production startup.

## Why out-of-process first
MoonRay and Blender carry large native dependency graphs. Loading MoonRay directly into Blender can create symbol/ABI conflicts and turns a renderer crash into a DCC crash. Process isolation makes early integration safer and permits restart/recovery. If Phase 10 proves transport to be the dominant bottleneck, an in-process variant may be evaluated under a new ADR.

## Consequences
### Positive
- Removes OpenUSD/Hydra ABI from the primary production runtime path.
- Gives project direct control over scene translation, incremental updates, framebuffer/AOV transport and error recovery.
- Better matches the desired `Render Engine → MoonRay` product experience.
- Enables explicit performance instrumentation across each bridge stage.

### Costs
- We own Blender→MoonRay scene translation.
- We own bridge lifecycle, protocol/schema, incremental-update logic and framebuffer presentation.
- Material parity requires explicit engineering rather than relying on Hydra conventions.
- Project scope increases materially from L/High to XL/High.

## Rejected as primary
- Blender Hydra → hdMoonray → MoonRay: retained as fallback/reference/benchmark.
- External batch RDL/USD only: does not satisfy Blender-native workflow.
- In-process MoonRay library on day one: rejected due crash/ABI risk before performance evidence.

## Revisit triggers
- direct bridge is blocked by unstable/unusable MoonRay APIs;
- measured transport overhead remains unacceptable after optimized shared-memory/native data paths;
- official maintained Blender/MoonRay direct integration becomes available;
- Hydra path demonstrably meets all product goals with substantially lower maintenance and comparable/better measured performance.
