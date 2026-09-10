# Phase 06 — Geometry, transforms, camera and lights translation

Status: IN PROGRESS

## Goal
Establish deterministic scene translation for production-relevant geometry, transforms, camera and core lights.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Meshes, normals, UVs needed by later materials.
- Object/world transforms.
- Instances baseline if required for geometry architecture or defer details to Phase 07.
- Camera/lens/clipping mapping.
- Area/point/sun/spot or explicitly supported light set.
- Update/delete semantics.

## Out of scope
- Complex shader networks.
- Viewport optimization beyond correctness.
- Volumes/hair unless explicitly pulled in by accepted requirements.

## Tasks
- [ ] Create canonical translation schema.
- [ ] Build scene fixture tests.
- [ ] Validate coordinate systems/unit conventions.
- [ ] Validate edit/update/delete.
- [ ] Document unsupported object/light types.

## Acceptance criteria
- [ ] Reference fixtures match expected transforms/camera framing.
- [ ] Supported light types render predictably.
- [ ] Object add/update/delete is correct.
- [ ] Unsupported types fail or fall back explicitly, never silently mis-render.

## Verification
- Automated translation tests.
- Rendered fixture comparisons/metrics.
- Scene-update logs.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/06-geometry-camera-lights.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
