# Phase 07 — Materials, textures and instances

Status: PLANNED

## Goal
Implement and document a production-useful Blender material/texture subset mapped to MoonRay shaders plus robust instancing.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Principled-oriented supported subset.
- Image textures, UV selection, normal/bump path where feasible.
- Color/roughness/metallic/transmission subset as accepted.
- Material assignment/multi-material meshes.
- Object/collection instancing where supported.
- Texture invalidation/update semantics.

## Out of scope
- Claiming arbitrary Blender nodes work.
- Full Cycles shader parity.
- Unvalidated MaterialX catch-all.

## Tasks
- [ ] Define explicit support matrix.
- [ ] Implement mapping layer with unit tests.
- [ ] Create material fixture scenes.
- [ ] Handle missing textures and unsupported nodes predictably.
- [ ] Benchmark instance memory/translation basics.

## Acceptance criteria
- [ ] Supported material fixtures render within defined visual expectations.
- [ ] Unsupported nodes are surfaced explicitly.
- [ ] Texture reload/update works for accepted cases.
- [ ] Instances do not expand unexpectedly when native instancing is supported/selected.

## Verification
- Fixture renders.
- Translation unit tests.
- Support-matrix review.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/07-materials-textures-instances.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
