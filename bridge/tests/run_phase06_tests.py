#!/usr/bin/env python3
"""Phase 06 bridge smoke tests -- exercises the structured scene protocol
(CREATE_SCENE/scene_variables, UPDATE_OBJECT, UPDATE_CAMERA) against the real
bridge binary and the real MoonRay runtime, per docs/bridge/SCENE_TRANSLATION.md
/ ADR-0005. No mocking of the bridge process or MoonRay.

Builds one small hand-authored scene entirely through the wire protocol (no
.rdla file at all): a flat quad lit by an axis-aligned DistantLight (the proven
-good case from docs/evidence/phase05/sphere-light-investigation/), then
exercises update (move the quad) and delete (remove the quad, confirm the
render goes dark) to cover Phase 06's "Validate edit/update/delete" acceptance
criterion at the protocol level, independent of Blender/addon code.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))
from bridge_client import BridgeClient, read_framebuffer_f32  # noqa: E402

BRIDGE_BIN = os.environ.get("PHASE06_BRIDGE_BIN", "/root/moonray-blender/build/bridge06/moonray_bridge")
LOG_DIR = os.environ.get("PHASE06_LOG_DIR", "/root/moonray-blender/logs/phase06-build")
RDL2_DSO_PATH = os.environ.get(
    "PHASE06_RDL2_DSO_PATH", "/root/moonray-blender/install/openmoonray/rdl2dso"
)

_results = []


def record(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{(' -- ' + detail) if detail else ''}")
    _results.append((name, ok, detail))
    if not ok:
        raise SystemExit(f"PHASE06_TEST_FAILED: {name}: {detail}")


def bridge_env():
    env = dict(os.environ)
    env["RDL2_DSO_PATH"] = RDL2_DSO_PATH
    env["REZ_MOONRAY_ROOT"] = "/root/moonray-blender/install/openmoonray"
    return env


_PHASE06_VMEM_CAP_KB = 24 * 1024 * 1024


def spawn_bridge(socket_path: str, log_path: str):
    proc = subprocess.Popen(
        ["bash", "-c", f'ulimit -v {_PHASE06_VMEM_CAP_KB}; exec "$0" "$@"', BRIDGE_BIN,
         "--socket", socket_path, "--log-dir", LOG_DIR],
        env=bridge_env(),
        stdout=open(log_path, "ab"),
        stderr=subprocess.STDOUT,
    )
    deadline = time.time() + 40.0
    while time.time() < deadline:
        if os.path.exists(socket_path):
            return proc
        if proc.poll() is not None:
            raise RuntimeError(f"bridge exited early with code {proc.returncode}, see {log_path}")
        time.sleep(0.1)
    proc.kill()
    raise RuntimeError(f"bridge did not create socket {socket_path} within timeout")


# --- Fixture scene ----------------------------------------------------------
# A flat quad in the RDL2 Y-up XZ plane (y=0, facing +Y), lit from straight
# above by a DistantLight -- the exact axis-aligned direction proven to shade
# correctly in docs/evidence/phase05/sphere-light-investigation/ test 9.
QUAD_VERTICES = [
    [-1.0, 0.0, -1.0],
    [1.0, 0.0, -1.0],
    [1.0, 0.0, 1.0],
    [-1.0, 0.0, 1.0],
]
QUAD_INDICES = [0, 1, 2, 0, 2, 3]  # 2 triangles, CCW seen from +Y
QUAD_TRANSFORM_IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
QUAD_TRANSFORM_MOVED = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 3, 0, 0, 1]  # shifted +3 in X

# Camera at (0, 3, 0) looking straight down (-Y); local vz maps to world +Y so
# local -Z (the camera's forward axis) points world -Y.
CAMERA_TRANSFORM = [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 3, 0, 1]

# DistantLight direction straight down. DistantLight's update() (moonray/lib/
# rendering/pbr/light/DistantLight.cc, pinned commit) composes node_xform with
# a built-in 180-degree rotation about local X ("for consistency with
# DiskLight") before deriving the actual illumination direction -- root-caused
# in Phase 06 (see docs/evidence/phase06/light-orientation-fix/), superseding
# Phase 05's un-root-caused axis-snap workaround. To make the light actually
# travel toward world (0, -1, 0), node_xform's basis vectors must each have
# their Y/Z components negated relative to the naive "Z axis = direction"
# construction (addon/scene_translator.py::light_xform_to_rdl2_mat4) --
# this literal matrix is that correction already applied by hand.
LIGHT_TRANSFORM_STRAIGHT_DOWN = [0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1]


def build_base_scene(c: BridgeClient):
    c.hello()
    ack = c.create_scene({"image_width": 64, "image_height": 64, "pixel_samples": 8})
    record("CREATE_SCENE: structured scaffold accepted", ack["payload"].get("ok") is True, json.dumps(ack))

    cam_ack = c.update_camera({
        "name": "cam",
        "transform": CAMERA_TRANSFORM,
        "focal": 30.0,
        "film_width_aperture": 24.0,
        "near": 0.1,
        "far": 100.0,
    })
    record("UPDATE_CAMERA: accepted", cam_ack["payload"].get("ok") is True, json.dumps(cam_ack))

    mesh_ack = c.update_object({
        "op": "create",
        "kind": "mesh",
        "name": "quad",
        "transform": QUAD_TRANSFORM_IDENTITY,
        "vertices_by_index": QUAD_INDICES,
        "face_vertex_count": [3, 3],
        "vertex_list": QUAD_VERTICES,
    })
    record("UPDATE_OBJECT (mesh create): accepted", mesh_ack["payload"].get("ok") is True, json.dumps(mesh_ack))

    light_ack = c.update_object({
        "op": "create",
        "kind": "light",
        "name": "sun",
        "light_class": "DistantLight",
        "transform": LIGHT_TRANSFORM_STRAIGHT_DOWN,
        "color": [1.0, 1.0, 1.0],
        "intensity": 3.0,
    })
    record("UPDATE_OBJECT (light create): accepted", light_ack["payload"].get("ok") is True, json.dumps(light_ack))


def render_and_read(c: BridgeClient):
    reply = c.start_render("final")
    stats = reply["payload"]
    buf = read_framebuffer_f32(stats["shm_name"], stats["width"], stats["height"], stats["channels"])
    return stats, buf


def test_create_populate_render(socket_path: str):
    with BridgeClient(socket_path) as c:
        build_base_scene(c)
        stats, buf = render_and_read(c)
        lo, hi = min(buf), max(buf)
        has_nan_or_inf = any(v != v or v in (float("inf"), float("-inf")) for v in (lo, hi))
        record(
            "structured scene: renders, non-constant, non-NaN pixel content",
            (hi > lo) and not has_nan_or_inf,
            f"min={lo} max={hi} dims={stats.get('width')}x{stats.get('height')}",
        )
        # Center pixel should see the lit quad (bright), not background black.
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        cx, cy = w // 2, h // 2
        idx = (cy * w + cx) * ch
        center_luma = sum(buf[idx:idx + 3]) / 3.0
        record(
            "structured scene: center pixel (over the lit quad) is not flat black",
            center_luma > 0.05,
            f"center_luma={center_luma}",
        )
        return center_luma


def test_update_moves_geometry(socket_path: str, lit_center_luma: float):
    with BridgeClient(socket_path) as c:
        build_base_scene(c)
        c.start_render("final")  # first render, establishes mInitialized

        move_ack = c.update_object({
            "op": "update",
            "kind": "mesh",
            "name": "quad",
            "transform": QUAD_TRANSFORM_MOVED,
            "vertices_by_index": QUAD_INDICES,
            "face_vertex_count": [3, 3],
            "vertex_list": QUAD_VERTICES,
        })
        record("UPDATE_OBJECT (mesh update/move): accepted", move_ack["payload"].get("ok") is True, json.dumps(move_ack))

        stats, buf = render_and_read(c)
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        cx, cy = w // 2, h // 2
        idx = (cy * w + cx) * ch
        center_luma = sum(buf[idx:idx + 3]) / 3.0
        record(
            "update: after moving the quad out of frame, center pixel goes dark",
            center_luma < 0.05,
            f"center_luma={center_luma} (was {lit_center_luma} before the move)",
        )


def test_delete_removes_geometry(socket_path: str, lit_center_luma: float):
    # Delete happens BEFORE the first START_RENDER -- this is the case Phase 06
    # actually needs (bridge_launcher launches one fresh bridge process per
    # Blender render; the add-on never mutates a scene that has already been
    # initialize()d/rendered once). Deleting AFTER a render already happened
    # in the SAME live RenderContext was tried and does NOT reliably remove
    # the geometry from a second render -- RenderContext::startFrame()'s
    # mSceneUpdated path uses rt::ChangeFlag::UPDATE (not ALL), and
    # GeometryManager's UPDATE path is additive/refresh-oriented, not proven
    # to shrink an already-built BVH when a GeometrySet member is removed.
    # That is a real, open limitation for Phase 08's incremental viewport to
    # solve (likely via forcing ChangeFlag::ALL on a delete, or another
    # RenderContext API not yet identified) -- not claimed fixed here.
    with BridgeClient(socket_path) as c:
        build_base_scene(c)

        del_ack = c.update_object({"op": "delete", "kind": "mesh", "name": "quad"})
        record("UPDATE_OBJECT (mesh delete): accepted", del_ack["payload"].get("ok") is True, json.dumps(del_ack))

        stats, buf = render_and_read(c)
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        cx, cy = w // 2, h // 2
        idx = (cy * w + cx) * ch
        center_luma = sum(buf[idx:idx + 3]) / 3.0
        record(
            "delete-before-first-render: center pixel is dark (GeometrySet invariant honored)",
            center_luma < 0.05,
            f"center_luma={center_luma} (would be ~{lit_center_luma} if not deleted)",
        )


def test_unsupported_light_class_rejected(socket_path: str):
    with BridgeClient(socket_path) as c:
        build_base_scene(c)
        from bridge_client import BridgeError
        try:
            c.update_object({
                "op": "create",
                "kind": "light",
                "name": "bogus",
                "light_class": "NotARealLightClass",
                "transform": QUAD_TRANSFORM_IDENTITY,
                "color": [1, 1, 1],
                "intensity": 1.0,
            })
            record("unsupported light_class: rejected with ERROR", False, "no error raised")
        except BridgeError as e:
            record(
                "unsupported light_class: rejected with ERROR category 2",
                e.category == 2,
                f"category={e.category} code={e.code} message={e.message}",
            )


def main():
    log_dir_local = "/tmp/phase06-tests"
    os.makedirs(log_dir_local, exist_ok=True)
    socket_path = f"{log_dir_local}/bridge.sock"
    log_path = f"{log_dir_local}/bridge.log"
    os.makedirs(LOG_DIR, exist_ok=True)

    if os.path.exists(socket_path):
        os.remove(socket_path)
    proc = spawn_bridge(socket_path, log_path)
    try:
        lit_luma = test_create_populate_render(socket_path)
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    if os.path.exists(socket_path):
        os.remove(socket_path)
    proc = spawn_bridge(socket_path, log_path)
    try:
        test_update_moves_geometry(socket_path, lit_luma)
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    if os.path.exists(socket_path):
        os.remove(socket_path)
    proc = spawn_bridge(socket_path, log_path)
    try:
        test_delete_removes_geometry(socket_path, lit_luma)
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    if os.path.exists(socket_path):
        os.remove(socket_path)
    proc = spawn_bridge(socket_path, log_path)
    try:
        test_unsupported_light_class_rejected(socket_path)
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    passed = sum(1 for _, ok, _ in _results if ok)
    print(f"\nPHASE06_TESTS_OK: {passed}/{len(_results)} checks passed")


if __name__ == "__main__":
    main()
