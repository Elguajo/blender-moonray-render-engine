# SphereLight / non-axis-aligned DistantLight investigation (Phase 05)

Observed 2026-09-10 inside `MoonRay-Rocky9`, against the pinned Phase 03/04
runtime, via `bridge/build/bridge04/moonray_bridge` (Phase 04 binary,
unmodified) and a series of hand-authored `.rdla` scenes fed to it through
`addon/bridge_client.py`. This is a real-render investigation (every result
below is an observed pixel buffer, not a prediction) into two anomalies hit
while implementing `addon/scene_writer.py`'s light translation. Both are
worked around in that module (see its docstring "Light type: DistantLight,
not SphereLight" and "Light direction is snapped to the nearest world axis");
neither is claimed fixed at the engine level, and neither blocks Phase 05's
own acceptance criteria (F12 renders a correct image).

## Timeline of tests

All renders used the same `RdlMeshGeometry` cube translated from Blender's
factory-default `Cube` object (verified independently correctly wound: cross
products of each face's first triangle were computed by hand from the emitted
`vertex_list_0`/`vertices_by_index` and match the geometrically correct
outward normal for all four faces checked) and the same `DwaBaseMaterial`
(`albedo = Rgb(0.6, 0.6, 0.6)`, all other attributes default), unless noted.

1. **`SphereLight` translated from Blender's default point light** (position
   + heuristic intensity, `radius` from `shadow_soft_size`): camera-visible
   faces rendered flat black; a small bright streak was visible along one
   silhouette edge (a grazing specular response, not diffuse). Raw pixel
   sampling (10x10 grid across the frame, plus a full-frame histogram)
   confirmed genuine near-zero values, not a display/tonemap artifact.
2. **Same scene, `intensity` raised 100x** (10 -> 1000): the bright streak's
   peak value scaled linearly (~46 -> ~4664, matching the 100x change
   exactly), but the flat-black majority of the image was unchanged -- ruling
   out a pure magnitude/exposure problem.
3. **`EnvLight` substituted for the same `SphereLight`, same geometry**: the
   cube rendered correctly -- a smooth, physically plausible per-face
   gradient (different flat shading per face, consistent with view-angle-
   dependent Fresnel response under a uniform environment). This proved mesh
   winding, material setup and the render pipeline itself were not at fault.
4. **A brand-new, hand-placed `SphereLight`** (simple round-number position,
   large radius, large intensity, `normalized=false` to bypass the
   `apply_scene_scale` area/intensity computation entirely -- see
   `moonray/lib/rendering/pbr/light/LightUtil.h computeLightRadiance` and
   `SphereLight.cc`'s `mInvArea`/`sApplySceneScaleKey` handling, read from the
   pinned source to rule out a scene-scale misunderstanding): still flat
   black on the cube, confirming the problem was not specific to the
   Blender-derived light's numbers.
5. **The known-good Phase 03/04 reference scene (`testdata/rectangle.rdla`)
   with only its light swapped for a `SphereLight`** (same position style as
   test 4, on the camera side of the rectangle): rendered correctly --
   visible diffuse shading plus a specular highlight. This isolated the
   failure to something about geometry authored by this module, not
   `SphereLight` itself.
6. **The same reference rectangle, `SphereLight` moved much farther away
   along the same axis**: still rendered correctly (dimmer, as expected) --
   ruled out light-to-surface distance as the variable.
7. **The reference rectangle's exact scene, only its material's `albedo`
   changed from `bind(AttributeMap(...))` to a literal `Rgb(0.6, 0.6, 0.6)`**
   (matching this module's own material): rendered correctly but visibly
   dimmer than the `AttributeMap`-bound version -- literal-vs-bound albedo
   changes brightness but does not zero it, so it does not explain test 1's
   flat black either.
8. **A minimal flat 2-triangle quad** (this module's own vertex-authoring
   code path, structurally identical to the reference rectangle, normal
   independently verified outward) **lit by a `SphereLight` placed directly
   above along the surface normal** (an unambiguous, maximally-favorable
   case): still flat black. This ruled out "closed 12-triangle box"
   self-shadowing as the variable (test used only 2 triangles) and reconfirmed
   the issue reproduces on this module's own geometry-authoring path
   specifically, independent of light distance/position/intensity/
   normalization.
9. **`DistantLight` substituted for `SphereLight`, full cube scene, direction
   pointing straight down** (`node_xform` built from a hand-verified
   orthonormal axis-aligned matrix): rendered correctly -- bright top face,
   correctly dark side faces, matching the expected physical result for a
   downward directional light. This is the light type/pattern
   `addon/scene_writer.py` now uses.
10. **The same `DistantLight` approach, but with a non-axis-aligned direction**
    (a clean, hand-verified orthonormal, right-handed 45-degree-tilted
    `node_xform`, confirmed via dot-product hand-checks that both the
    top face and the tilted geometry in test 8's flat-quad variant should
    receive strong, non-grazing illumination): flat black again, on both the
    cube and the isolated flat-quad case. This is the second, independent
    anomaly: even `DistantLight`, proven to work for axis-aligned directions
    in test 9, fails for a non-trivial (but still mathematically verified
    orthonormal, correctly-oriented, right-handed) direction.

## What was ruled out

- Mesh winding / outward normal direction (hand-verified via cross products
  for every face checked; also indirectly proven by `EnvLight` and the
  axis-aligned `DistantLight` both shading the same geometry correctly).
- `scene_scale` / `apply_scene_scale` misunderstanding (source-code-verified
  formula, and bypassed entirely in test 4 via `normalized=false` with no
  change in outcome).
- Light-to-surface distance (tests 4, 6, 8 span very different distances,
  all black under `SphereLight`; test 6 at long distance still worked
  correctly under the reference geometry).
- Closed-volume self-occlusion (test 8 uses an open 2-triangle quad).
- Literal-vs-`bind(AttributeMap(...))` material albedo (test 7 shows this
  changes brightness, not an on/off switch).
- The general render pipeline / bridge / material system (both `EnvLight` and
  an axis-aligned `DistantLight` light the exact same geometry and material
  correctly).

## What was not isolated

The exact mechanism by which (a) `SphereLight` specifically fails on
geometry authored by this module's `RdlMeshGeometry` construction (while
working on the pre-existing reference scene) and (b) a non-axis-aligned
`DistantLight` node_xform specifically fails regardless of geometry, were
not root-caused. Both symptoms look mechanically similar (a light that,
geometrically, should illuminate a visible surface instead contributes
nothing), which may or may not share a common cause with each other -- not
established either way. Chasing this further (e.g. with `gdb`, as Phase 04's
real use-after-free bug was root-caused) is explicitly out of Phase 05's
scope (`docs/phases/05-blender-renderengine-integration.md`: "ONLY minimal
translation of one baseline scene"). It is a real, reproducible MoonRay-side
(or MoonRay-build-side) anomaly worth a focused follow-up or an upstream
report if it resurfaces in a later phase (materials/lights translation,
Phase 06/07).

## Workaround shipped in Phase 05

`addon/scene_writer.py` translates the Blender point light as an
axis-snapped `DistantLight`:
1. Compute a direction from the light's position toward the primitive's
   centroid (a reasonable directional approximation of "where the light is
   relative to the subject", not a hardcoded constant).
2. Snap that direction to whichever single world axis it is closest to
   (`_snap_to_axis`), guaranteeing the emitted `node_xform` is always one of
   the basis-permutation matrices proven to render correctly in test 9.

For Blender's own default scene (light positioned above the default cube),
this reproduces exactly the "straight down" case already verified in test 9
-- see [`../f12-gui-render.png`](../f12-gui-render.png) for the resulting F12
render inside the real Blender GUI.
