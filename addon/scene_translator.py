"""Blender scene -> structured bridge protocol messages (Phase 06).

Replaces Phase 05's `scene_writer.py` (which wrote a self-contained `.rdla`
text file and passed its path to `CREATE_SCENE`): Phase 06 extended the
bridge protocol to a structured schema (docs/bridge/SCENE_TRANSLATION.md,
ADR-0005) -- `CREATE_SCENE` now takes `scene_variables` only, and
`UPDATE_OBJECT`/`UPDATE_CAMERA` carry the actual mesh/camera/light data as
JSON, translated directly into RDL2 SceneObjects natively in the bridge
(bridge/src/SceneBuilder.cpp), not by round-tripping through ASCII text.

General translation: any number of mesh objects, any number of supported
lights, exactly one active camera -- not Phase 05's exactly-one-of-each.
Unsupported object/light types raise SceneTranslationError before any bridge
call is made (ERROR_MODEL.md category 1: fail before native mutation).

## Coordinate convention (carried over from scene_writer.py, unchanged)
Blender is Z-up, right-handed. RDL2/MoonRay is Y-up, right-handed:
(x, y, z)_blender -> (x, z, -y)_moonray, a fixed +90-degree rotation about X
applied identically to positions and to each basis-vector column of a
transform matrix.

## Light orientation: the RotateX180 correction (Phase 06 root-cause fix)
Phase 05 found DistantLight/SphereLight anomalies (flat black on this
project's own geometry) and shipped an axis-snapped-direction workaround
without root-causing them (docs/evidence/phase05/sphere-light-investigation/).
Phase 06 root-caused the DistantLight/SpotLight/RectLight/DiskLight part of
it, confirmed against source (`moonray/lib/rendering/pbr/light/*.cc` at the
pin in UPSTREAM_LOCK.json) *and* empirically (two independent hand-built
scenes through the unmodified Phase 04 bridge -- one axis-aligned, one
tilted -- both went from flat 0.0 to correctly lit once the fix below was
applied): every one of those four light classes' `update()` composes the
`node_xform`-derived frame with a built-in 180-degree rotation about the
frame's own local X axis ("for consistency with DiskLight", per that
source's own comments) before deriving the light's actual illumination
direction. A `node_xform` built by naively pointing its local +Z at the
intended direction therefore illuminates the direction's mirror image about
local X instead. The fix (`light_xform_to_rdl2_mat4` below) negates the Y/Z
components of each of the three orientation basis vectors -- but NOT the
translation -- after the normal axis conversion, cancelling the engine's own
rotation so the authored `node_xform` produces the *intended* world-space
illumination direction for arbitrary (not just axis-aligned) orientations.
This is a bug in this project's own light-transform construction, not a
MoonRay defect -- no upstream report is warranted. `SphereLight` has no
orientation-dependent illumination (purely positional) and was empirically
confirmed unaffected by the original anomaly; the same correction is still
applied to it for consistency (harmless: it only affects sidedness/texture
framing, not basic illumination), since the underlying `sRotateX180` exists
in `SphereLight.cc` too.

**Only DistantLight was independently re-rendered end-to-end (both an
axis-aligned and a tilted case) after this fix. SpotLight/RectLight/DiskLight
receive the identical, source-verified correction but were not independently
re-rendered in Phase 06** -- flag this if a similar anomaly resurfaces for
those classes; the fix mechanism is proven, but per-class end-to-end
verification is not.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple


class SceneTranslationError(RuntimeError):
    """The active Blender scene contains something Phase 06 does not support
    (an unsupported light/camera type, a mesh with no triangulated faces,
    etc). Raised before any bridge call -- mirrors ERROR_MODEL.md category 1.
    """


# ---------------------------------------------------------------------------
# Coordinate conversion (unchanged from Phase 05's scene_writer.py)
# ---------------------------------------------------------------------------

def _convert_axis(v: Sequence[float]) -> Tuple[float, float, float]:
    """Blender Z-up (x, y, z) -> RDL2/MoonRay Y-up (x, z, -y)."""
    return (float(v[0]), float(v[2]), -float(v[1]))


def _rotate_x180(v: Sequence[float]) -> Tuple[float, float, float]:
    """180-degree rotation about the local X axis, applied in already-
    RDL2-Y-up space: negates Y and Z, leaves X unchanged. See module
    docstring "Light orientation: the RotateX180 correction"."""
    return (float(v[0]), -float(v[1]), -float(v[2]))


def matrix_to_rdl2_mat4(m) -> Tuple[float, ...]:
    """Converts a Blender world matrix (mathutils.Matrix, 4x4, point-as-
    column-vector convention: p_world = m @ p_local) into the 16 floats RDL2
    Mat4(...)/node_xform expects: vx, vy, vz (converted local-axis
    directions, w=0), then vw (converted translation, w=1). Used for meshes
    and the camera -- NOT for lights, which need light_xform_to_rdl2_mat4
    below instead."""
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


def light_xform_to_rdl2_mat4(m) -> Tuple[float, ...]:
    """Like matrix_to_rdl2_mat4, but additionally applies the RotateX180
    correction (see module docstring) to the three orientation basis vectors.
    Use for every RDL2 light class's node_xform; never for meshes/camera."""
    cols = [(m[0][j], m[1][j], m[2][j]) for j in range(4)]
    vx = _rotate_x180(_convert_axis(cols[0]))
    vy = _rotate_x180(_convert_axis(cols[1]))
    vz = _rotate_x180(_convert_axis(cols[2]))
    vw = _convert_axis(cols[3])
    return (
        vx[0], vx[1], vx[2], 0.0,
        vy[0], vy[1], vy[2], 0.0,
        vz[0], vz[1], vz[2], 0.0,
        vw[0], vw[1], vw[2], 1.0,
    )


# ---------------------------------------------------------------------------
# Per-object visibility (docs/bridge/SCENE_TRANSLATION.md "Per-object
# visibility contract" -- Geometry.cc source-verified: side_type default
# TWO_SIDED=0, nine visible_* defaulting true). Blender's per-object
# ray-visibility flags map close to one-to-one; unset flags are simply
# omitted so the RDL2 default (all visible, two-sided) applies.
# ---------------------------------------------------------------------------

def _visibility_fields(obj) -> dict:
    vis = getattr(obj, "visible_camera", True)
    fields = {"visible_in_camera": bool(vis)}
    # Blender's ray-visibility flags (Object.visible_*) cover camera/diffuse/
    # glossy/transmission/shadow/volume scatter individually since 2.8x; map
    # what exists 1:1, leave the rest (glossy/transmission split, mirror_*)
    # at their RDL2 defaults since Blender has no matching per-object split.
    if hasattr(obj, "visible_diffuse"):
        fields["visible_diffuse_reflection"] = bool(obj.visible_diffuse)
        fields["visible_diffuse_transmission"] = bool(obj.visible_diffuse)
    if hasattr(obj, "visible_glossy"):
        fields["visible_glossy_reflection"] = bool(obj.visible_glossy)
        fields["visible_glossy_transmission"] = bool(obj.visible_glossy)
    if hasattr(obj, "visible_transmission"):
        fields["visible_mirror_transmission"] = bool(obj.visible_transmission)
    if hasattr(obj, "visible_shadow"):
        fields["visible_shadow"] = bool(obj.visible_shadow)
    if hasattr(obj, "visible_volume_scatter"):
        fields["visible_volume"] = bool(obj.visible_volume_scatter)
    return fields


# ---------------------------------------------------------------------------
# Mesh extraction
# ---------------------------------------------------------------------------

def _extract_mesh(obj) -> dict:
    mesh = obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles) == 0:
            raise SceneTranslationError(f"mesh object {obj.name!r} has no triangulated faces to render")

        vertex_list = [_convert_axis(v.co) for v in mesh.vertices]
        indices: List[int] = []
        uv_list: List[Tuple[float, float]] = []
        normal_list: List[Tuple[float, float, float]] = []

        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        # Blender 4.1+ removed Mesh.calc_normals_split() (split normals are
        # computed on demand now); mesh.loops[i].normal is valid without it.

        for tri in mesh.loop_triangles:
            indices.extend(tri.vertices)
            for loop_index in tri.loops:
                nx, ny, nz = mesh.loops[loop_index].normal
                normal_list.append(_convert_axis((nx, ny, nz)))
                if uv_layer is not None:
                    u, v = uv_layer[loop_index].uv
                    uv_list.append((u, v))

        payload = {
            "op": "create",
            "kind": "mesh",
            "name": obj.name,
            "transform": list(matrix_to_rdl2_mat4(obj.matrix_world)),
            "vertices_by_index": indices,
            "face_vertex_count": [3] * (len(indices) // 3),
            "vertex_list": [list(v) for v in vertex_list],
            "normal_list": [list(n) for n in normal_list],
        }
        if uv_layer is not None and len(uv_list) == len(normal_list):
            payload["uv_list"] = [list(uv) for uv in uv_list]
        payload.update(_visibility_fields(obj))
        return payload
    finally:
        obj.to_mesh_clear()


# ---------------------------------------------------------------------------
# Camera extraction (docs/bridge/SCENE_TRANSLATION.md "Camera" table)
# ---------------------------------------------------------------------------

def _extract_camera(cam_obj) -> dict:
    data = cam_obj.data
    if data.type != 'PERSP':
        raise SceneTranslationError(
            f"Phase 06 only supports perspective cameras (scene.camera.data.type == {data.type!r}); "
            "orthographic/panoramic camera translation is later-phase scope"
        )

    payload = {
        "name": cam_obj.name,
        "transform": list(matrix_to_rdl2_mat4(cam_obj.matrix_world)),
        "focal": float(data.lens),
        "film_width_aperture": float(data.sensor_width),
        "near": max(float(data.clip_start), 1e-4),
        "far": float(data.clip_end),
        # pixel_aspect_ratio (RDL2 wants pixel y/x, the inverse of Blender's
        # pixel_aspect_x/pixel_aspect_y) needs scene.render, not camera data
        # -- filled in by extract_scene() after this call returns.
    }

    # shift_x/shift_y are fractions of the LARGER sensor dimension in
    # Blender; RDL2's film offsets are in the same physical units as
    # film_width_aperture (mm). This is a plausible, not render-fixture-
    # verified, unit mapping (SCENE_TRANSLATION.md: "Open -- Phase 06").
    payload["horizontal_film_offset"] = float(data.shift_x) * float(data.sensor_width)
    payload["vertical_film_offset"] = float(data.shift_y) * float(data.sensor_width)

    if data.dof.use_dof:
        payload["dof"] = True
        fstop = max(float(data.dof.aperture_fstop), 0.01)
        payload["dof_aperture"] = float(data.lens) / fstop  # aperture width in mm, plausible not fixture-verified
        focus_obj = data.dof.focus_object
        if focus_obj is not None:
            focus_distance = (focus_obj.matrix_world.translation - cam_obj.matrix_world.translation).length
        else:
            focus_distance = max(float(data.dof.focus_distance), 1e-4)
        payload["dof_focus_distance"] = float(focus_distance)

    return payload


# ---------------------------------------------------------------------------
# Light extraction (native Blender type -> RDL2 light class, per
# docs/bridge/SCENE_TRANSLATION.md's confirmed table -- decision B: map
# Blender's own light.type rather than replacing it with a MoonRay-native
# enum, so scenes stay portable to Cycles/EEVEE)
# ---------------------------------------------------------------------------

def _extract_light(obj) -> dict:
    data = obj.data
    xform = list(light_xform_to_rdl2_mat4(obj.matrix_world))
    color = list(data.color)
    common = {
        "op": "create",
        "kind": "light",
        "name": obj.name,
        "transform": xform,
        "color": color,
    }

    if data.type == 'POINT':
        common["light_class"] = "SphereLight"
        # Pragmatic, not radiometrically exact (SCENE_TRANSLATION.md: exact
        # Blender-power -> RDL2-intensity conversion is explicitly Open).
        # Watts / 4*pi approximates radiant intensity (power per steradian).
        common["intensity"] = max(float(data.energy) / (4.0 * math.pi), 0.001)
        common["attrs"] = {"radius": max(float(data.shadow_soft_size), 1e-4)}
    elif data.type == 'SUN':
        common["light_class"] = "DistantLight"
        # SUN's energy is already an irradiance (W/m^2), not total power --
        # use directly rather than Phase 05's ad hoc /500 point-light heuristic.
        common["intensity"] = max(float(data.energy), 0.001)
        common["attrs"] = {"angular_extent": max(math.degrees(float(data.angle)), 1e-3)}
    elif data.type == 'SPOT':
        common["light_class"] = "SpotLight"
        common["intensity"] = max(float(data.energy) / (4.0 * math.pi), 0.001)
        outer_deg = math.degrees(float(data.spot_size))
        inner_deg = outer_deg * (1.0 - float(data.spot_blend))
        common["attrs"] = {
            "inner_cone_angle": max(inner_deg, 0.0),
            "outer_cone_angle": max(outer_deg, 0.01),
            "lens_radius": max(float(data.shadow_soft_size), 1e-4),
        }
    elif data.type == 'AREA':
        shape = data.shape
        width = max(float(data.size), 1e-4)
        height = max(float(getattr(data, "size_y", data.size)), 1e-4) if shape == 'RECTANGLE' else width
        area = width * height if shape != 'DISK' else math.pi * (width / 2.0) ** 2
        intensity = max(float(data.energy) / max(area, 1e-6), 0.001)
        if shape in ('SQUARE', 'RECTANGLE'):
            common["light_class"] = "RectLight"
            common["intensity"] = intensity
            common["attrs"] = {"width": width, "height": height}
        elif shape == 'DISK':
            common["light_class"] = "DiskLight"
            common["intensity"] = intensity
            common["attrs"] = {"radius": width / 2.0}
        else:
            # ELLIPSE has no RDL2 equivalent primitive -- fail explicitly
            # rather than silently substitute Disk/Rect
            # (docs/bridge/SCENE_TRANSLATION.md "Lights").
            raise SceneTranslationError(
                f"light object {obj.name!r} is an AREA light with shape 'ELLIPSE', "
                "which has no RDL2 light-class equivalent at the pinned MoonRay version; "
                "use SQUARE/RECTANGLE/DISK instead"
            )
    else:
        raise SceneTranslationError(f"light object {obj.name!r} has unsupported light type {data.type!r}")

    return common


# ---------------------------------------------------------------------------
# Top-level scene extraction
# ---------------------------------------------------------------------------

def extract_scene(depsgraph) -> dict:
    """Validates and extracts every supported object in `depsgraph` into the
    structured payloads write_via_bridge() below sends. Raises
    SceneTranslationError on anything unsupported, before any bridge call."""
    scene = depsgraph.scene
    cam_obj = scene.camera
    if cam_obj is None or cam_obj.type != 'CAMERA':
        raise SceneTranslationError("scene has no active camera (scene.camera is unset)")

    mesh_objs = [o for o in depsgraph.objects if o.type == 'MESH']
    light_objs = [o for o in depsgraph.objects if o.type == 'LIGHT']
    if len(mesh_objs) == 0:
        raise SceneTranslationError("scene has no mesh objects to render")
    if len(light_objs) == 0:
        raise SceneTranslationError("scene has no light objects (MoonRay needs at least one to render anything visible)")

    camera_payload = _extract_camera(cam_obj)
    # pixel_aspect_ratio needs scene.render (not camera data): RDL2 wants
    # pixel y/x, Blender's render settings carry pixel_aspect_x/_y (inverse).
    render = scene.render
    camera_payload["pixel_aspect_ratio"] = float(render.pixel_aspect_y) / float(render.pixel_aspect_x)

    mesh_payloads = [_extract_mesh(o) for o in mesh_objs]
    light_payloads = [_extract_light(o) for o in light_objs]

    return {
        "camera": camera_payload,
        "meshes": mesh_payloads,
        "lights": light_payloads,
    }


def write_via_bridge(client, depsgraph, *, image_width: int, image_height: int, pixel_samples: int) -> dict:
    """Extracts the scene and sends it over an already-connected bridge
    client as CREATE_SCENE + UPDATE_CAMERA + one UPDATE_OBJECT per mesh/light.
    Every render is a fresh bridge process (bridge_launcher one-shot
    lifecycle), so this always sends 'create' -- incremental update/delete
    across a single long-lived session is Phase 08 viewport scope; the wire
    protocol itself already supports it (bridge/tests/run_phase06_tests.py).
    Returns the extracted scene dict (useful for logging/diagnostics)."""
    scene = extract_scene(depsgraph)

    client.create_scene({
        "image_width": int(image_width),
        "image_height": int(image_height),
        "pixel_samples": int(pixel_samples),
    })
    client.update_camera(scene["camera"])
    for mesh_payload in scene["meshes"]:
        client.update_object(mesh_payload)
    for light_payload in scene["lights"]:
        client.update_object(light_payload)

    return scene
