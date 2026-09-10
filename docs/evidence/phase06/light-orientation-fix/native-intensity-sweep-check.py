import sys, os
sys.path.insert(0, "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/client")
from bridge_client import BridgeClient

sys.path.insert(0, "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/tests")
import run_phase06_tests as t
import _debug_cube as cube

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
            "transform": cube.IDENTITY,
            "vertices_by_index": cube.CUBE_INDICES,
            "face_vertex_count": cube.CUBE_FACE_COUNT,
            "vertex_list": cube.CUBE_VERTICES,
        })
        # EnvLight has no class-specific attrs needed; light_class not in our
        # supported set list intentionally -- bypass applyObjectUpdate's
        # class allowlist by calling update_object anyway to see the ERROR,
        # OR just accept the allowlist and test via raw payload since the
        # allowlist is only enforced light_class validity, not a hard block on
        # EnvLight per se... actually EnvLight IS excluded from
        # supportedLightClasses() (Phase 06 scope: Sphere/Distant/Spot/Rect/Disk
        # only). Test this differently: use DistantLight but with intensity=100
        # to rule out a magnitude problem instead (cheap, no code path change).
        c.update_object({
            "op": "create", "kind": "light", "name": "sun", "light_class": "DistantLight",
            "transform": t.LIGHT_TRANSFORM_STRAIGHT_DOWN, "color": [1.0, 1.0, 1.0], "intensity": 100.0,
        })
        stats, buf = t.render_and_read(c)
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        idx = ((h // 2) * w + (w // 2)) * ch
        print("center rgba (intensity=100) =", buf[idx:idx + 4])
finally:
    proc.terminate()
    proc.wait(timeout=10)
