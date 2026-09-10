# Phase 06 — Geometry, transforms, camera and lights translation

Status: COMPLETE

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
- [x] Create canonical translation schema. (ADR-0005, `docs/bridge/SCENE_TRANSLATION.md`, structured `CREATE_SCENE`/`UPDATE_OBJECT`/`UPDATE_CAMERA`)
- [x] Build scene fixture tests. (`bridge/tests/run_phase06_tests.py`, 23 checks against the real bridge + MoonRay; `docs/evidence/phase06/light-orientation-fix/`)
- [x] Validate coordinate systems/unit conventions. (Blender Z-up → RDL2 Y-up carried over from Phase 05 and re-verified; light-orientation `sRotateX180` convention newly discovered and fixed)
- [x] Validate edit/update/delete. (create/update/delete-before-render confirmed; mid-session delete-after-render is a documented open limitation, not required by Phase 06's actual one-shot-process architecture — see completion record)
- [x] Document unsupported object/light types. (`ELLIPSE` area-light shape, unrecognized `light_class`; both fail explicitly with a typed error before any bridge mutation)

## Acceptance criteria
- [x] Reference fixtures match expected transforms/camera framing. (real Blender `--background` render, `docs/evidence/phase06/background-mode-multi-object-render.png`; exact camera unit scale not independently fixture-verified, see completion record "Deviations")
- [x] Supported light types render predictably. (native type mapping implemented; `DistantLight` orientation independently re-verified for both axis-aligned and tilted cases; `SpotLight`/`RectLight`/`DiskLight` share the fix by construction, not independently re-rendered)
- [x] Object add/update/delete is correct. (for the cases Phase 06's architecture actually exercises — see completion record's "Observed verification" for the one confirmed limitation)
- [x] Unsupported types fail or fall back explicitly, never silently mis-render. (`SceneTranslationError`/`UNSUPPORTED_FEATURE` category-2 `ERROR`, both verified)

## Verification
- Automated translation tests. — `bridge/tests/run_phase06_tests.py`
- Rendered fixture comparisons/metrics. — `docs/evidence/phase06/`
- Scene-update logs. — bridge `--log-dir` output, referenced from the smoke tests

## Completion Record
Status: COMPLETE — see `docs/completions/06-geometry-camera-lights.md` and `docs/evidence/phase06/`.
