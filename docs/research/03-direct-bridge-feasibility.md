# Research — Direct MoonRay Bridge Feasibility

Status: ARCHITECTURE EVIDENCE / IMPLEMENTATION NOT YET VERIFIED
Date: 2026-09-09

## Finding
A direct DCC bridge is technically plausible without writing a new renderer. MoonRay itself remains the renderer; the project builds the integration and scene-translation layer.

## MoonRay-facing evidence
Current MoonRay source exposes `moonray::rndr::RenderContext` as the top-level rendering access point. Its API includes, among other capabilities:
- initialization;
- scene update from RDL data/file between renders;
- geometry update hooks;
- `startFrame()`;
- `requestStop()` / `stopFrame()`;
- render-buffer snapshots;
- AOV/render-output snapshots;
- cryptomatte/deep-buffer accessors.

This is sufficient evidence to justify a native bridge prototype. It is **not** yet evidence that every API is stable/public enough for long-term third-party DCC support; Phase 03/04 must validate exact build/export/link behavior.

## Blender-facing requirement
The integration should use Blender's custom RenderEngine lifecycle for:
- selectable engine registration;
- final render lifecycle;
- viewport update/draw lifecycle;
- RenderResult/pass integration;
- cancellation/progress.

Exact Blender 5.2 API behavior must be verified during Phase 05 against current official API/source and by running Blender.

## Performance position
Do not claim Direct Bridge will outperform Hydra before measurement. The direct path is selected primarily for control, independence from Hydra/USD ABI and fit to the desired DCC integration. Phase 10 owns benchmark evidence.

## Primary design risk
The largest engineering cost moves from USD/Hydra ABI matching to:
- high-volume scene-data transport;
- deterministic Blender→RDL2 mapping;
- incremental update classification;
- material translation;
- progressive framebuffer/AOV presentation;
- process lifecycle and crash recovery.

## Baseline recommendation
Start out-of-process, CPU-only, final-frame first. Add viewport and aggressive incremental optimization only after the minimal render loop is proven.
