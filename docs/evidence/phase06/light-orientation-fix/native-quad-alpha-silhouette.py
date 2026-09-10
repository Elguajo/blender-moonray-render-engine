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
        t.build_base_scene(c)
        stats, buf = t.render_and_read(c)
        w, h, ch = stats["width"], stats["height"], stats["channels"]
        print("dims", w, h, ch)
        for row in range(0, h, 1):
            line = ""
            for col in range(0, w, 1):
                idx = (row * w + col) * ch
                a = buf[idx + 3]
                line += "#" if a > 0.5 else " "
            print(line)
finally:
    proc.terminate()
    proc.wait(timeout=10)
