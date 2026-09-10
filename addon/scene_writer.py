"""Minimal Blender scene -> .rdla translator for Phase 05.

Scope (docs/phases/05-blender-renderengine-integration.md): "ONLY minimal
translation of one baseline scene (camera + primitive + light -- not general
geometry/material translation, that is Phase 06/07)". This module accepts
exactly one active camera, exactly one mesh object and exactly one supported
light, and writes them as an RDL2 ASCII (.rdla) scene file that the existing
Phase 04 `moonray_bridge` CREATE_SCENE (bridge/src/RenderSession.cpp) can load
as-is -- Phase 05 deliberately reuses the full-.rdla-path CREATE_SCENE
contract rather than extending the bridge protocol (see
docs/bridge/MESSAGE_SCHEMA.md "Open -- Phase 04/06/07" on per-message payload
field layout, and NEXT_SESSION.md option (a): "writing a minimal .rdla from
Python by base scene and pass path").

RDL2 ASCII object/attribute names and required scene shape (SceneVariables,
GeometrySet, Layer 8-tuple, LightSet) were confirmed against the known-good
Phase 03/04 reference scene (testdata/rectangle.rdla) and against the
installed runtime's own SceneClass introspection
(`rdl2_print -c BoxGeometry -c DistantLight -c PerspectiveCamera -c
DwaBaseMaterial -c SceneVariables`), not guessed from memory -- see
docs/completions/05-blender-renderengine-integration.md.

## Light direction is snapped to the nearest world axis (load-bearing)
A second, independent reproducible issue was found on top of the SphereLight
one: an *arbitrary* (non-axis-aligned) `DistantLight` node_xform -- even a
mathematically verified orthonormal, right-handed, correctly-oriented one --
also renders the same flat 0.0 black on simple, correctly-wound geometry in
this build, while a purely axis-aligned direction (basis vectors that are
signed permutations of the world axes, e.g. straight down) renders correctly
every time it was tried (docs/evidence/phase05/sphere-light-investigation/).
Rather than chase a second engine-level anomaly outside Phase 05's scope,
`extract_baseline_scene` snaps the computed light-to-primitive direction to
whichever single world axis it is closest to (`_snap_to_axis`) before
building the node_xform. This is a real, if coarse, simplification of the
light's actual direction (never a hardcoded constant), and it degrades
gracefully: Blender's own default scene light sits mostly above the default
cube, so the snapped direction is "straight down" -- visually the same key
light angle the un-snapped computation would have picked, just exact instead
of approximate.

## Light type: DistantLight, not SphereLight (load-bearing, read before
## "fixing" this back to a point light)
Blender's default light is a POINT light, and a literal RDL2 SphereLight is
the obvious direct mapping -- that was the first implementation. It was
dropped after reproducible end-to-end evidence
(docs/evidence/phase05/sphere-light-investigation/) that a `SphereLight` in
this exact pinned MoonRay build fails to illuminate an `RdlMeshGeometry` authored
by this module (camera-visible faces render as flat 0.0 black) under a wide
sweep of positions/distances/radii/intensities/normalized settings, while the
*same* geometry lights correctly under `EnvLight` and `DistantLight`, and the
known-good reference scene (testdata/rectangle.rdla) only reproduces the
SphereLight failure once its material's `albedo` is changed from
`bind(AttributeMap(...))` to a literal `Rgb(...)` (still dims rather than
zeroing there, unlike our geometry). The exact root cause was not isolated
(mesh-winding, primitive_attributes presence, and light-to-surface distance
were each tested and ruled out individually) and is out of Phase 05's scope to
chase further (`docs/phases/05-blender-renderengine-integration.md` is
explicitly "minimal translation of one baseline scene", not a MoonRay engine
bug hunt). `DistantLight` was verified end-to-end to shade our translated cube
correctly (bright top face toward the light, correctly dark side faces) and is
used instead. Point lights are approximated as a single directional light
aimed from the light's position toward the primitive's centroid -- see
`extract_baseline_scene`'s direction computation and `light_intensity`'s
comment. Exact point-light photometry (falloff, radius) is out of scope until
this is revisited (Phase 06/07/09, or a dedicated MoonRay upstream report).

## Coordinate convention (load-bearing, read before touching this file)
Blender is Z-up, right-handed. RDL2/MoonRay is Y-up, right-handed (confirmed
from testdata/rectangle.rdla: a near-identity camera node_xform sits at
positive Z looking toward Z=0 geometry that spans Y in [0, 1] -- Y is
"vertical" there). Converting one to the other is a fixed +90 degree rotation
about X (Rx(-90) in the "rotate the world" sense): (x, y, z)_blender ->
(x, z, -y)_moonray. This is a pure rotation (determinant +1, handedness
preserved), applied identically to positions and to each of a node_xform's
three basis-vector columns -- see `_convert_axis`/`matrix_to_rdl2_mat4`.
Camera-local convention (looks down local -Z, +Y up) is shared between
Blender and RDL2, so no additional per-object local-axis flip is needed on
top of this single world-frame rotation.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple


class SceneTranslationError(RuntimeError):
    """The active Blender scene doesn't fit Phase 05's minimal supported
    shape (exactly one camera + one mesh + one supported light). Raised
    before any bridge/RDL2 interaction -- mirrors ERROR_MODEL.md category 1
    ("fail validation before native renderer mutation") on the add-on side.
    """


# ---------------------------------------------------------------------------
# Coordinate conversion
# ---------------------------------------------------------------------------

def _convert_axis(v: Sequence[float]) -> Tuple[float, float, float]:
    """Blender Z-up (x, y, z) -> RDL2/MoonRay Y-up (x, z, -y). Used for both
    positions and basis-vector directions (see module docstring)."""
    return (float(v[0]), float(v[2]), -float(v[1]))


def _sub(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _normalize(v: Sequence[float]) -> Tuple[float, float, float]:
    length = (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5
    if length < 1e-9:
        raise SceneTranslationError("light-to-primitive direction is degenerate (zero length)")
    return (v[0] / length, v[1] / length, v[2] / length)


def _snap_to_axis(v: Sequence[float]) -> Tuple[float, float, float]:
    """Snaps a direction to the nearest signed world axis (see module
    docstring "Light direction is snapped to the nearest world axis")."""
    ax, ay, az = abs(v[0]), abs(v[1]), abs(v[2])
    if ax >= ay and ax >= az:
        return (1.0 if v[0] >= 0 else -1.0, 0.0, 0.0)
    if ay >= ax and ay >= az:
        return (0.0, 1.0 if v[1] >= 0 else -1.0, 0.0)
    return (0.0, 0.0, 1.0 if v[2] >= 0 else -1.0)


def direction_to_rdl2_mat4(direction: Sequence[float]) -> Tuple[float, ...]:
    """Builds an RDL2 node_xform Mat4 (16 floats) whose local +Z axis (RDL2
    DistantLight's own convention: `mDirection = mFrame.getZ()`, confirmed in
    moonray/lib/rendering/pbr/light/DistantLight.cc) points along `direction`
    (already in RDL2/Y-up space). Roll around that axis is arbitrary for a
    DistantLight (radially symmetric aside from its small default
    angular_extent), so any orthonormal right-handed completion is valid --
    this uses a standard Gram-Schmidt basis build against a fixed up
    reference, swapped to avoid a near-parallel degenerate case."""
    dz = _snap_to_axis(_normalize(direction))
    up_ref = (0.0, 1.0, 0.0) if abs(dz[1]) < 0.99 else (1.0, 0.0, 0.0)
    vx = _normalize(_cross(up_ref, dz))
    vy = _cross(dz, vx)
    return (
        vx[0], vx[1], vx[2], 0.0,
        vy[0], vy[1], vy[2], 0.0,
        dz[0], dz[1], dz[2], 0.0,
        0.0, 0.0, 0.0, 1.0,
    )


def matrix_to_rdl2_mat4(m) -> Tuple[float, ...]:
    """Converts a Blender world matrix (mathutils.Matrix, 4x4, point-as-
    column-vector convention: p_world = m @ p_local) into the 16 floats RDL2
    Mat4(...) expects: vx, vy, vz (converted local-axis directions, w=0),
    then vw (converted translation, w=1) -- matching testdata/rectangle.rdla's
    `Mat4(1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0.5,2.28...,1)` layout (4 rows of 4:
    3 basis directions then translation, row-vector/last-row-translation
    convention)."""
    cols = [(m[0][j], m[1][j], m[2][j]) for j in range(4)]
    vx = _convert_axis(cols[0])
    vy = _convert_axis(cols[1])
    vz = _convert_axis(cols[2])
    vw = _convert_axis(cols[3])
    return (
        vx[0], vx[1], vx[2], 0.0,
        vy[0], vy[1], vy[2], 0.0,
        vz[0], vz[1], vz[2], 0.0,
        vw[0], vw[1], vw[2], 1.0,
    )


# ---------------------------------------------------------------------------
# RDL2 ASCII formatting helpers
# ---------------------------------------------------------------------------

def _fmt(x: float) -> str:
    return repr(float(x))


def _vec3(v: Sequence[float]) -> str:
    return f"Vec3({_fmt(v[0])}, {_fmt(v[1])}, {_fmt(v[2])})"


def _rgb(c: Sequence[float]) -> str:
    return f"Rgb({_fmt(c[0])}, {_fmt(c[1])}, {_fmt(c[2])})"


def _mat4(vals16: Sequence[float]) -> str:
    return "Mat4(" + ", ".join(_fmt(v) for v in vals16) + ")"


def _quote(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Scene extraction (reads the Blender depsgraph; no bpy-specific typing so
# this stays testable from a plain background-mode script)
# ---------------------------------------------------------------------------

def extract_baseline_scene(depsgraph):
    """Validates and extracts the one supported camera/mesh/light triple from
    `depsgraph`. Raises SceneTranslationError on anything outside Phase 05's
    scope. Returns a plain dict describing everything write_rdla() needs,
    decoupled from live bpy objects (which become invalid once to_mesh_clear
    runs)."""
    scene = depsgraph.scene
    cam_obj = scene.camera
    if cam_obj is None or cam_obj.type != 'CAMERA':
        raise SceneTranslationError(
            "scene has no active camera (scene.camera is unset); MoonRay Phase 05 requires one"
        )
    cam_data = cam_obj.data
    if cam_data.type != 'PERSP':
        raise SceneTranslationError(
            f"Phase 05 only supports perspective cameras (scene.camera.data.type == {cam_data.type!r}); "
            "orthographic/panoramic camera translation is later-phase scope"
        )

    mesh_objs = [o for o in depsgraph.objects if o.type == 'MESH']
    light_objs = [o for o in depsgraph.objects if o.type == 'LIGHT']

    if len(mesh_objs) != 1:
        raise SceneTranslationError(
            f"Phase 05 supports exactly one mesh object in the scene (found {len(mesh_objs)}); "
            "general multi-object geometry translation is Phase 06 scope"
        )
    if len(light_objs) != 1:
        raise SceneTranslationError(
            f"Phase 05 supports exactly one light object in the scene (found {len(light_objs)}); "
            "general light translation is Phase 06 scope"
        )

    mesh_obj = mesh_objs[0]
    light_obj = light_objs[0]
    if light_obj.data.type != 'POINT':
        raise SceneTranslationError(
            f"Phase 05 only supports POINT lights (light object {light_obj.name!r} is "
            f"{light_obj.data.type!r}); other light types are Phase 06 scope"
        )

    mesh = mesh_obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles) == 0:
            raise SceneTranslationError(f"mesh object {mesh_obj.name!r} has no triangulated faces to render")

        world_matrix = mesh_obj.matrix_world
        vertex_list: List[Tuple[float, float, float]] = [
            _convert_axis(world_matrix @ v.co) for v in mesh.vertices
        ]
        indices: List[int] = []
        for tri in mesh.loop_triangles:
            indices.extend(tri.vertices)
    finally:
        mesh_obj.to_mesh_clear()

    cam_xform = matrix_to_rdl2_mat4(cam_obj.matrix_world)

    # DistantLight has no position of its own (see module docstring on why
    # SphereLight was dropped) -- approximate the Blender point light as a
    # single directional light aimed from its position toward the primitive's
    # centroid, computed here in already-converted RDL2 space so no second
    # axis conversion is needed.
    mesh_centroid = (
        sum(v[0] for v in vertex_list) / len(vertex_list),
        sum(v[1] for v in vertex_list) / len(vertex_list),
        sum(v[2] for v in vertex_list) / len(vertex_list),
    )
    light_pos = _convert_axis(light_obj.matrix_world.translation)
    light_direction = _sub(mesh_centroid, light_pos)
    light_xform = direction_to_rdl2_mat4(light_direction)

    return {
        "mesh_name": mesh_obj.name,
        "mesh_vertex_list": vertex_list,
        "mesh_indices": indices,
        "cam_name": cam_obj.name,
        "cam_xform16": cam_xform,
        "cam_focal": float(cam_data.lens),
        "cam_film_width": float(cam_data.sensor_width),
        "cam_near": max(float(cam_data.clip_start), 1e-4),
        "cam_far": float(cam_data.clip_end),
        "light_name": light_obj.name,
        "light_xform16": light_xform,
        "light_color": tuple(light_obj.data.color),
        # DistantLight "intensity" (normalized=true, the default) has no
        # area/distance term to calibrate against -- it is a flat brightness
        # multiplier. energy/500 was chosen because it reproduces the exact
        # value (2.0) verified end-to-end against Blender's default 1000 W
        # point light and default-scene camera/object scale
        # (docs/evidence/phase05/sphere-light-investigation/); it is a
        # pragmatic scale, not a radiometric unit conversion (a directional
        # light has no physical "distance" to a point light's Watts to
        # convert from in the first place). Exact photometric matching
        # remains out of scope until point lights are revisited.
        "light_intensity": max(float(light_obj.data.energy) / 500.0, 0.01),
    }


# ---------------------------------------------------------------------------
# RDL2 ASCII scene emission
# ---------------------------------------------------------------------------

def write_rdla(path: str, scene_data: dict, *, image_width: int, image_height: int, pixel_samples: int) -> None:
    geo_name = "geo"
    mat_name = "material"
    layer_name = "defaultLayer"
    geomset_name = "geometrySet"
    lightset_name = "lightSet"

    indices = scene_data["mesh_indices"]
    face_vertex_count = ", ".join("3" for _ in range(len(indices) // 3))
    vidx = ", ".join(str(i) for i in indices)
    vlist = ", ".join(_vec3(v) for v in scene_data["mesh_vertex_list"])

    lines: List[str] = []
    lines.append("SceneVariables {")
    lines.append(f'    ["camera"] = PerspectiveCamera({_quote(scene_data["cam_name"])}),')
    lines.append(f'    ["image_width"] = {int(image_width)},')
    lines.append(f'    ["image_height"] = {int(image_height)},')
    lines.append(f'    ["pixel_samples"] = {int(pixel_samples)},')
    lines.append("}")
    lines.append("")
    lines.append(f'RdlMeshGeometry({_quote(geo_name)}) {{')
    lines.append(f'    ["vertices_by_index"] = {{{vidx}}},')
    lines.append(f'    ["vertex_list_0"] = {{{vlist}}},')
    lines.append(f'    ["face_vertex_count"] = {{{face_vertex_count}}},')
    lines.append('    ["is_subd"] = false,')
    lines.append("}")
    lines.append("")
    lines.append(f'GeometrySet({_quote(geomset_name)}) {{')
    lines.append(f'    RdlMeshGeometry({_quote(geo_name)}),')
    lines.append("}")
    lines.append("")
    lines.append(f'Layer({_quote(layer_name)}) {{')
    lines.append(
        f'    {{RdlMeshGeometry({_quote(geo_name)}), "", DwaBaseMaterial({_quote(mat_name)}), '
        f'LightSet({_quote(lightset_name)}), undef(), undef(), undef(), undef()}},'
    )
    lines.append("}")
    lines.append("")
    lines.append(f'DwaBaseMaterial({_quote(mat_name)}) {{')
    lines.append('    ["albedo"] = Rgb(0.6, 0.6, 0.6),')
    lines.append("}")
    lines.append("")
    lines.append(f'DistantLight({_quote(scene_data["light_name"])}) {{')
    lines.append(f'    ["node_xform"] = {_mat4(scene_data["light_xform16"])},')
    lines.append(f'    ["color"] = {_rgb(scene_data["light_color"])},')
    lines.append(f'    ["intensity"] = {_fmt(scene_data["light_intensity"])},')
    lines.append("}")
    lines.append("")
    lines.append(f'LightSet({_quote(lightset_name)}) {{')
    lines.append(f'    DistantLight({_quote(scene_data["light_name"])}),')
    lines.append("}")
    lines.append("")
    lines.append(f'PerspectiveCamera({_quote(scene_data["cam_name"])}) {{')
    lines.append(f'    ["node_xform"] = {_mat4(scene_data["cam_xform16"])},')
    lines.append(f'    ["near"] = {_fmt(scene_data["cam_near"])},')
    lines.append(f'    ["far"] = {_fmt(scene_data["cam_far"])},')
    lines.append(f'    ["focal"] = {_fmt(scene_data["cam_focal"])},')
    lines.append(f'    ["film_width_aperture"] = {_fmt(scene_data["cam_film_width"])},')
    lines.append("}")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_scene(depsgraph, path: str, *, image_width: int, image_height: int, pixel_samples: int) -> dict:
    """Convenience entry point: extract + write in one call. Returns the
    extracted scene_data dict (useful for logging/diagnostics)."""
    scene_data = extract_baseline_scene(depsgraph)
    write_rdla(path, scene_data, image_width=image_width, image_height=image_height, pixel_samples=pixel_samples)
    return scene_data
