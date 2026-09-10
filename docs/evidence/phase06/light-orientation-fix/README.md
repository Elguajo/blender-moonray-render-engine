# Light orientation root-cause (Phase 06)

Root-causes and fixes the DistantLight/SphereLight anomaly Phase 05 found but
did not root-cause (`docs/evidence/phase05/sphere-light-investigation/`),
worked around there with an un-root-caused axis-snapped-direction hack. This
directly answers Phase 06's pre-approved decision C.

## Root cause

`moonray/lib/rendering/pbr/light/{DistantLight,SpotLight,RectLight,DiskLight,
SphereLight}.cc::update()` (pinned commit `eef67ae9...`, per `UPSTREAM_LOCK.json`)
each compose the light's `node_xform`-derived local-to-render frame with a
built-in 180-degree rotation about the frame's own local X axis
(`sRotateX180`), explicitly "to maintain consistency with DiskLight" per that
source's own comments (`DistantLight.cc` lines ~238-249, ~380, ~416-417;
grep-confirmed present in all five classes' `.cc` files). This means the
direction a light actually illuminates along is **not** `node_xform`'s raw
local-Z-axis column -- it is that column (and, for shape-carrying classes
like RectLight/DiskLight, the whole orthonormal basis) with its Y and Z
components negated.

`addon/scene_writer.py`'s `direction_to_rdl2_mat4()` (Phase 05) built
`node_xform` assuming the naive "local +Z = intended direction" convention,
so every `DistantLight` it emitted illuminated the mirror image (about local
X) of the intended direction. This is a bug in this project's own
light-transform construction code, confirmed and fixed here -- **not a
MoonRay engine defect**; no upstream report is warranted.

## Evidence

All runs below used the unmodified Phase 04 `moonray_bridge` binary
(`bridge/build/bridge04/moonray_bridge`) loading hand-authored `.rdla` text,
to isolate the finding from any Phase 06 C++/Python code (`bridge/src/SceneBuilder.cpp`,
`addon/scene_translator.py`). Buffer values are read directly from the
published shared-memory framebuffer, not estimated.

| # | Scene (`.rdla`) | Runner | Result |
|---|---|---|---|
| 1 | [`01-cube-distant-straight-down-naive.rdla.txt`](01-cube-distant-straight-down-naive.rdla.txt) — closed cube, `DistantLight` node_xform built the naive way for "straight down" | [`run-01-naive.py`](run-01-naive.py) | Center pixel `(0, 0, 0, 1)` -- flat black, alpha=1 confirms the cube *is* hit by camera rays; reproduces Phase 05's anomaly via the ASCII path with a brand-new scene, ruling out a Phase 06 C++ bug |
| 2 | [`02-cube-envlight-control.rdla.txt`](02-cube-envlight-control.rdla.txt) — same cube/camera, `EnvLight` instead | [`run-02-env-control.py`](run-02-env-control.py) | Center pixel `≈(1.003, 1.003, 1.003, 1)` -- confirms geometry/camera/material are all correct; only the directional light is broken |
| 3 | [`03-cube-distant-straight-down-corrected.rdla.txt`](03-cube-distant-straight-down-corrected.rdla.txt) — same scene, `node_xform`'s basis Y/Z-negated per the fix | [`run-03-corrected-straight-down.py`](run-03-corrected-straight-down.py) | Center pixel `≈(3.05, 3.05, 3.05, 1)` -- matches `intensity=3.0`, correctly lit |
| 4 | [`04-cube-distant-tilted-corrected.rdla.txt`](04-cube-distant-tilted-corrected.rdla.txt) — same scene, a **non-axis-aligned** tilted direction, corrected | [`run-04-corrected-tilted.py`](run-04-corrected-tilted.py) | Center pixel `≈(1.66, 1.66, 1.66, 1)` -- nonzero, plausible partial-angle brightness; confirms the fix generalizes beyond axis-aligned directions (Phase 05's *second*, independent anomaly) |
| 5 | [`05-cube-spherelight-control.rdla.txt`](05-cube-spherelight-control.rdla.txt) — same cube, `SphereLight` positioned above, this module's own geometry-authoring code | [`run-05-spherelight-control.py`](run-05-spherelight-control.py) | Center pixel `≈(318.8, 318.8, 318.8, 1)` -- bright (SphereLight has no orientation-dependent illumination, so the `sRotateX180` quirk doesn't manifest as "flat black" for it; Phase 05's original SphereLight failure was not reproduced by this straightforward "light above, looking down" case and is left as a separate, unresolved question if it resurfaces with real Blender-derived data) |

The `native-*.py` scripts (run against the Phase 06 native `SceneBuilder.cpp`
path, `bridge/build/bridge06/moonray_bridge`) are the original investigation
trail that led to this finding -- a flat 2-triangle quad under a
straight-down `DistantLight` (the naive convention) rendering exactly flat
black (`native-quad-*`), ruled out several alternative hypotheses (missing
normals: `native-quad-explicit-normals-check.py`; magnitude:
`native-intensity-sweep-check.py`), before the closed-cube ASCII control
tests above isolated the cause to the light-transform convention itself
rather than anything mesh- or Phase-06-specific.

## Fix

`addon/scene_translator.py::light_xform_to_rdl2_mat4()` applies the
correction (negate Y/Z of each of the three orientation basis vectors, after
the normal Blender-Z-up -> RDL2-Y-up axis conversion, translation
untouched) for every light's `node_xform`. Used for all five supported RDL2
light classes (`SphereLight`/`DistantLight`/`SpotLight`/`RectLight`/
`DiskLight`) for consistency, even though only `DistantLight` was
independently re-rendered end-to-end here (twice: axis-aligned and tilted).
Phase 05's axis-snap workaround (`_snap_to_axis`) is removed entirely --
the corrected construction is exact for arbitrary orientations, not just
axis-aligned ones, so no snapping is needed.

## What remains open

- `SpotLight`/`RectLight`/`DiskLight` receive the identical, source-verified
  correction but were **not** independently re-rendered in Phase 06 -- if a
  similar anomaly resurfaces for one of them, re-run this same style of
  isolated `EnvLight`-vs-direct-light control test before assuming a new bug.
- SphereLight's *original* Phase 05 failure (on this module's own geometry,
  with Blender-derived position/intensity) was not reproduced by the
  straightforward control case here and remains unexplained if it resurfaces
  with real translated data -- worth a fresh, narrower investigation using
  Phase 05's exact original parameters if it happens again, rather than
  assuming this fix also covers it.
