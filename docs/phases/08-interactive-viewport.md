# Phase 08 — Interactive Rendered Viewport

Status: PLANNED

## Goal
Deliver progressive MoonRay rendering inside Blender Rendered Viewport with responsive camera/scene updates for the accepted feature subset.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- RenderEngine viewport lifecycle.
- Progressive beauty snapshots.
- Efficient frame transport/presentation.
- Camera interaction.
- Scene-change restart/update policy.
- Viewport resolution scaling and cancellation.

## Out of scope
- Final performance optimization beyond acceptance.
- All AOV viewport modes unless required.

## Tasks
- [ ] Implement progressive frame loop.
- [ ] Measure transport/copy/presentation costs.
- [ ] Avoid per-pixel Python loops.
- [ ] Test orbit/pan/zoom and object edits.
- [ ] Test bridge restart while viewport is active.

## Acceptance criteria
- [ ] Rendered Viewport shows progressive MoonRay output.
- [ ] Camera interaction updates without manual render command.
- [ ] Accepted scene edits update/restart correctly.
- [ ] UI remains usable within defined latency target.
- [ ] No persistent zombie renderer after viewport exit.

## Verification
- Interactive manual test matrix.
- Instrumentation timings.
- Longer viewport soak test.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/08-interactive-viewport.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
