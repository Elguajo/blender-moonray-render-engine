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
        maxv = -1.0
        maxidx = -1
        nonzero = 0
        for i in range(0, len(buf), ch):
            r, g, b, a = buf[i], buf[i+1], buf[i+2], buf[i+3]
            m = max(r, g, b)
            if m > maxv:
                maxv = m
                maxidx = i
            if m > 0.001:
                nonzero += 1
        px = (maxidx // ch) % w
        py = (maxidx // ch) // w
        print("max channel value", maxv, "at pixel", px, py, "rgba=", buf[maxidx:maxidx+4])
        print("nonzero(>0.001) pixel count", nonzero, "of", w*h)
        # also print alpha channel stats
        alphas = [buf[i+3] for i in range(0, len(buf), ch)]
        print("alpha min/max", min(alphas), max(alphas))
finally:
    proc.terminate()
    proc.wait(timeout=10)
