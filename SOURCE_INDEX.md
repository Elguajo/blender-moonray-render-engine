# Source Index — Direct MoonRay Bridge

Fast lookup table for the upstream C++ headers/sources most relevant to
**Direct MoonRay Bridge** development (`bridge/`), so an agent or contributor
doesn't have to grep across the whole MoonRay/scene_rdl2 tree for common
entry points.

## Status: upstream, not yet vendored

`moonray` and `scene_rdl2` are **not vendored into this repository**
(confirmed: no `moonray/` or `scene_rdl2/` source tree exists locally as of
this writing; see [`UPSTREAM_LOCK.json`](UPSTREAM_LOCK.json)). All paths
below are relative to the pinned upstream repos and were verified against
the exact pinned commit trees via the GitHub API on 2026-09-09:

| Repo | Pinned commit | Commit date |
|---|---|---|
| [OpenMoonRay/moonray](https://github.com/OpenMoonRay/moonray) | `eef67ae992b5037943a7716cca96ed443c36dcec` | 2026-07-15 |
| [OpenMoonRay/scene_rdl2](https://github.com/OpenMoonRay/scene_rdl2) | `1229d3eaa1ee41dc1ddefbe781c623edceafbac8` | 2026-08-18 |

**When Phase 03 (MoonRay native runtime) vendors or builds these sources
locally, re-point the paths below at the local checkout and drop this
caveat.** If `UPSTREAM_LOCK.json` pins change, re-verify every path here
against the new commit (`gh api repos/OpenMoonRay/<repo>/git/trees/<sha>?recursive=1`)
before trusting it — do not assume paths are stable across MoonRay releases
(see `CLAUDE.md`: "Never infer support solely from documentation").

Background reading before touching any of this: [`docs/vendor/openmoonray/developer-reference/source-structure.md`](docs/vendor/openmoonray/developer-reference/source-structure.md)
(repo layout) and [`docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md`](docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md)
(RDL2 API walkthrough).

---

## RenderContext (render session entry point)

The object that owns a `SceneContext`, drives rendering, and is the main
integration point for a host application (this is what `bridge/` will hold
a reference to).

- `moonray/lib/rendering/rndr/RenderContext.h` / `.cc`
  https://github.com/OpenMoonRay/moonray/blob/eef67ae992b5037943a7716cca96ed443c36dcec/lib/rendering/rndr/RenderContext.h
- `moonray/lib/rendering/rndr/RenderOptions.h` / `.cc` — options used to construct/configure a `RenderContext`
- `moonray/lib/rendering/rndr/RenderDriver.h` / `.cc` — internal render-loop driver owned by `RenderContext`
- `moonray/lib/rendering/rndr/FrameState.h` — per-frame state passed through the driver
- `moonray/lib/application/RaasApplication.h` / `.cc` — reference host application showing how to drive a `RenderContext` end-to-end (CLI renderer)

## RenderOutput (AOVs / frame buffer output)

- `moonray/lib/rendering/rndr/RenderOutputDriver.h` / `.cc` — drives writing configured `RenderOutput` scene objects to disk/buffers
- `moonray/lib/rendering/rndr/RenderOutputDriverImpl.h` — impl details (tile/channel layout)
- `moonray/lib/rendering/rndr/Film.h` / `.cc` — pixel buffer accumulation (what the bridge will read for progressive/interactive display)
- `moonray/lib/rendering/rndr/ImageWriteDriver.h` / `.cc` — final image write path
- `scene_rdl2/lib/scene/rdl2/RenderOutput.h` / `.cc` — the `RenderOutput` scene-object class/attributes themselves (AOV name, type, format)

## SceneContext (scene graph root)

- `scene_rdl2/lib/scene/rdl2/SceneContext.h` / `.cc`
  https://github.com/OpenMoonRay/scene_rdl2/blob/1229d3eaa1ee41dc1ddefbe781c623edceafbac8/lib/scene/rdl2/SceneContext.h
- `scene_rdl2/lib/scene/rdl2/SceneClass.h` / `.cc` — attribute schema for a class of scene objects
- `scene_rdl2/lib/scene/rdl2/SceneObject.h` / `.cc` — base class for every scene entity (get/set attributes, bindings)
- `scene_rdl2/lib/scene/rdl2/SceneVariables.h` / `.cc` — global render settings (resolution, camera pointer, frame, etc.)
- `scene_rdl2/lib/scene/rdl2/Attribute.h` / `.cc`, `AttributeKey.h` — typed attribute definitions and fast accessors
- Concept walkthrough: [`docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md`](docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md)

## RDL2 serialization (RDLA/RDLB read-write)

- `scene_rdl2/lib/scene/rdl2/AsciiReader.h` / `.cc`, `AsciiWriter.h` / `.cc` — RDLA (text) format
- `scene_rdl2/lib/scene/rdl2/BinaryReader.h` / `.cc`, `BinaryWriter.h` / `.cc` — RDLB (binary) format
- `scene_rdl2/lib/scene/rdl2/ValueContainerEnq.h` / `.cc`, `ValueContainerDeq.h` / `.cc` — low-level binary value (de)serialization primitives used by the binary reader/writer (likely candidates to reuse/mirror for the bridge's own IPC wire format)
- `scene_rdl2/lib/scene/rdl2/Dso.h` / `.cc`, `DsoFinder.h` / `.cc` — shared-library (DSO) loading for scene-class plugins, driven by `RDL2_DSO_PATH`

## Camera

- `scene_rdl2/lib/scene/rdl2/Camera.h` / `.cc` — base `Camera` scene-object attributes (near/far, node xform, motion steps)
- `moonray/lib/rendering/pbr/camera/Camera.h` / `.cc` — base render-time camera behavior
- `moonray/lib/rendering/pbr/camera/PerspectiveCamera.h` / `.cc` — most common case (Blender's default camera maps here)
- `moonray/lib/rendering/pbr/camera/OrthographicCamera.h` / `.cc`
- `moonray/lib/rendering/pbr/camera/ProjectiveCamera.h` / `.cc` — shared base for perspective/orthographic
- `moonray/lib/rendering/pbr/camera/FisheyeCamera.h` / `.cc`, `SphericalCamera.h` / `.cc`, `DomeMaster3DCamera.h` / `.cc` — other camera models
- `moonray/dso/camera/PerspectiveCamera/attributes.cc` — canonical example of declaring camera attributes on an RDL2 `SceneClass` (reference for how the bridge should populate camera scene objects)

## Geometry

- `scene_rdl2/lib/scene/rdl2/Geometry.h` / `.cc`, `GeometrySet.h` / `.cc` — RDL2-side geometry scene objects
- `moonray/lib/rendering/geom/Api.h` / `.cc` — main public geometry-construction API (this is what a Blender mesh translator calls into)
- `moonray/lib/rendering/geom/PolygonMesh.h` / `.cc` — polygon mesh primitive (primary target for Blender mesh export)
- `moonray/lib/rendering/geom/Primitive.h` / `.cc`, `PrimitiveGroup.h` / `.cc` — primitive base classes and grouping
- `moonray/lib/rendering/geom/Procedural.h` / `.cc`, `ProceduralLeaf.h` / `.cc`, `ProceduralContext.h` — procedural geometry generation hooks
- `moonray/lib/rendering/geom/Instance.h` / `.cc`, `InstanceProceduralLeaf.h` / `.cc` — instancing (Blender collection instances / particle instancing)
- `moonray/lib/rendering/geom/Curves.h` / `.cc`, `Points.h` / `.cc` — hair/curve and point-cloud primitives

## Materials / Shading

- `scene_rdl2/lib/scene/rdl2/Material.h` / `.cc`, `RootShader.h` / `.cc`, `Shader.h` / `.cc` — RDL2-side shader/material scene-object hierarchy
- `moonray/lib/rendering/shading/Material.h` / `.cc` — render-time material evaluation base class
- `moonray/lib/rendering/shading/MaterialApi.h` — public shading API surface for material DSOs
- `moonray/lib/rendering/shading/BsdfBuilder.h` / `.cc`, `BsdfComponent.h` / `.cc` — how a material composes BSDF lobes
- `moonray/lib/rendering/shading/bsdf/Bsdf.h` / `.cc` — BSDF base class; `bsdf/` subdir has individual lobe implementations (Lambert, OrenNayar, Mirror, etc.)
- Concept reference: [`docs/vendor/openmoonray/developer-reference/shaders/materials.md`](docs/vendor/openmoonray/developer-reference/shaders/materials.md), [`.../shaders/maps.md`](docs/vendor/openmoonray/developer-reference/shaders/maps.md)

---

## Maintenance

- This index only covers the categories requested for bridge work. Extend it
  (Lights, Layer/TraceSet, texturing) as those phases start — don't
  pre-populate speculatively.
- Every path here was checked to actually exist at the pinned commit; do not
  add a path from memory/training data — verify it first, per `CLAUDE.md`'s
  "never infer support solely from documentation" rule.
- **Verification is automated:** [`scripts/verify_source_index.py`](scripts/verify_source_index.py)
  re-fetches the real GitHub tree at the commits pinned in
  [`UPSTREAM_LOCK.json`](UPSTREAM_LOCK.json) and checks every path referenced
  above still exists there, and that this file's commit table/permalinks
  match the lock file. Run it any time `UPSTREAM_LOCK.json` changes, or
  before relying on this index for non-trivial work:

  ```bash
  python scripts/verify_source_index.py
  ```

  Not run automatically in CI (needs network access to the GitHub API) —
  same policy as `scripts/sync_openmoonray_docs.py`. Exit code 1 means the
  index has drifted; fix the flagged entries (and bump the commit
  table/permalinks if `UPSTREAM_LOCK.json` moved) before trusting it again.
