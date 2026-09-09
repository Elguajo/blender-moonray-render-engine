# Phase 09 — Final render, AOVs, animation and EXR

Status: PLANNED

## Goal
Complete Blender final-render workflow: F12, animation frame stepping, required passes/AOVs and EXR output for the accepted production subset.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Beauty final render.
- Required AOV/pass registration and transfer.
- Frame/animation state changes.
- EXR/Blender output integration.
- Cryptomatte/depth/normal classification where supported.
- Render cancellation/progress.

## Out of scope
- Render farm/distributed Arras.
- Unbounded AOV feature parity.

## Tasks
- [ ] Define required pass set.
- [ ] Map MoonRay AOV snapshots to Blender passes.
- [ ] Render multi-frame test.
- [ ] Validate EXR channels/naming/data ranges.
- [ ] Test cancel/restart across animation.

## Acceptance criteria
- [ ] Required passes appear in Blender and saved outputs.
- [ ] Multi-frame animation renders correct frame-dependent transforms.
- [ ] EXR validation passes for accepted channels.
- [ ] Failures/cancel do not corrupt later renders.

## Verification
- EXR channel inspection.
- Animation fixture comparison.
- RenderResult/pass tests.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/09-final-render-aovs-animation.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
