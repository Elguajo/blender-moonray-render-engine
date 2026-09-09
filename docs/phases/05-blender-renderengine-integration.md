# Phase 05 — Blender RenderEngine integration and first F12 frame

Status: PLANNED

## Goal
Register MoonRay as a Blender render engine and complete the first end-to-end F12 render through the Direct Bridge into Blender Render Result.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Blender add-on package.
- RenderEngine registration/UI.
- Bridge launch/version handshake.
- Minimal scene translation required for one baseline scene.
- F12 final render result.
- Cancel/error handling.

## Out of scope
- Rendered Viewport.
- Broad material support.
- Animation/AOV production parity.

## Tasks
- [ ] Verify Blender 5.2 RenderEngine API from official source/docs.
- [ ] Implement engine registration and settings panel.
- [ ] Translate baseline camera + primitive + light.
- [ ] Invoke bridge render.
- [ ] Copy result into Blender Render Result efficiently.
- [ ] Test cancel and bridge failure.

## Acceptance criteria
- [ ] `MoonRay` is selectable in Render Engine menu.
- [ ] Baseline .blend renders with F12 via MoonRay.
- [ ] Render result appears inside Blender without manual external render step.
- [ ] Cancel does not leave zombie bridge/render.
- [ ] Bridge failure is reported without taking Blender down.

## Verification
- Blender automated/background smoke where possible.
- Manual F12 GUI evidence.
- Logs proving MoonRay backend.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/05-blender-renderengine-integration.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
