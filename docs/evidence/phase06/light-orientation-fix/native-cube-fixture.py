import sys, os
sys.path.insert(0, "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/client")
from bridge_client import BridgeClient

sys.path.insert(0, "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/tests")
import run_phase06_tests as t

CUBE_VERTICES = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
]
CUBE_INDICES = [
    1, 2, 6, 1, 6, 5,   # +X
    0, 4, 7, 0, 7, 3,   # -X
    3, 7, 6, 3, 6, 2,   # +Y
    0, 1, 5, 0, 5, 4,   # -Y
    4, 5, 6, 4, 6, 7,   # +Z
    0, 3, 2, 0, 2, 1,   # -Z
]
CUBE_FACE_COUNT = [3] * 12
IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

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
        c.update_object({
            "op": "create", "kind": "mesh", "name": "cube",
            "transform": IDENTITY,
            "vertices_by_index": CUBE_INDICES,
            "face_vertex_count": CUBE_FACE_COUNT,
            "vertex_list": CUBE_VERTICES,
        })
        c.update_object({
            "op": "create", "kind": "light", "name": "sun", "light_class": "DistantLight",
            "transform": t.LIGHT_TRANSFORM_STRAIGHT_DOWN, "color": [1.0, 1.0, 1.0], "intensity": 3.0,
        })
        stats, buf = t.render_and_read(c)
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        idx = ((h // 2) * w + (w // 2)) * ch
        print("center rgba (closed cube, top face) =", buf[idx:idx + 4])
        # sample a grid to see distribution
        for row in range(0, h, 4):
            line = ""
            for col in range(0, w, 2):
                i = (row * w + col) * ch
                luma = sum(buf[i:i + 3]) / 3.0
                line += "#" if luma > 0.5 else ("." if luma > 0.05 else " ")
            print(line)
finally:
    proc.terminate()
    proc.wait(timeout=10)
