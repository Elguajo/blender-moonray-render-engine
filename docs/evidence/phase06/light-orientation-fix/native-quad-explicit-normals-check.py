import sys, os
sys.path.insert(0, "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/client")
from bridge_client import BridgeClient

sys.path.insert(0, "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/tests")
import run_phase06_tests as t

socket_path = "/tmp/phase06-tests/bridge.sock"
log_path = "/tmp/phase06-tests/bridge.log"
os.makedirs("/tmp/phase06-tests", exist_ok=True)
if os.path.exists(socket_path):
    os.remove(socket_path)
proc = t.spawn_bridge(socket_path, log_path)
try:
    with BridgeClient(socket_path) as c:
        c.hello()
        c.create_scene({"image_width": 64, "image_height": 64, "pixel_samples": 8})
        c.update_camera({
            "name": "cam", "transform": t.CAMERA_TRANSFORM,
            "focal": 30.0, "film_width_aperture": 24.0, "near": 0.1, "far": 100.0,
        })
        # 6 face-vertex normals (2 triangles x 3), all pointing +Y, matching
        # face_vertex_count/vertices_by_index's per-face-vertex convention.
        normals = [[0, 1, 0]] * 6
        c.update_object({
            "op": "create", "kind": "mesh", "name": "quad",
            "transform": t.QUAD_TRANSFORM_IDENTITY,
            "vertices_by_index": t.QUAD_INDICES,
            "face_vertex_count": [3, 3],
            "vertex_list": t.QUAD_VERTICES,
            "normal_list": normals,
        })
        c.update_object({
            "op": "create", "kind": "light", "name": "sun", "light_class": "DistantLight",
            "transform": t.LIGHT_TRANSFORM_STRAIGHT_DOWN, "color": [1.0, 1.0, 1.0], "intensity": 3.0,
        })
        stats, buf = t.render_and_read(c)
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        idx = ((h // 2) * w + (w // 2)) * ch
        print("center rgba (with explicit normals) =", buf[idx:idx + 4])
finally:
    proc.terminate()
    proc.wait(timeout=10)
