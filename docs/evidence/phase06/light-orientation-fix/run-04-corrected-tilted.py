import json, os, socket, struct, subprocess, sys, time, array

BRIDGE_BIN = "/root/moonray-blender/build/bridge04/moonray_bridge"
RDLA_PATH = "/mnt/d/01_DEV/blender-moonray-render-engine/bridge/tests/_debug_cube_tilted.rdla"
LOG_DIR = "/tmp/phase06-tests"
os.makedirs(LOG_DIR, exist_ok=True)
socket_path = f"{LOG_DIR}/bridge04.sock"
if os.path.exists(socket_path):
    os.remove(socket_path)

env = dict(os.environ)
env["RDL2_DSO_PATH"] = "/root/moonray-blender/install/openmoonray/rdl2dso"
env["REZ_MOONRAY_ROOT"] = "/root/moonray-blender/install/openmoonray"

proc = subprocess.Popen(
    ["bash", "-c", 'ulimit -v 24000000; exec "$0" "$@"', BRIDGE_BIN, "--socket", socket_path, "--log-dir", LOG_DIR],
    env=env, stdout=open(f"{LOG_DIR}/bridge04.log", "ab"), stderr=subprocess.STDOUT,
)
deadline = time.time() + 20
while time.time() < deadline and not os.path.exists(socket_path):
    time.sleep(0.1)

try:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect(socket_path)

    def send(type_, payload, id_="c1"):
        body = json.dumps({"protocol_version": 1, "type": type_, "id": id_, "payload": payload}).encode()
        sock.sendall(struct.pack("<I", len(body)) + body)

    def recv():
        (length,) = struct.unpack("<I", sock.recv(4))
        return json.loads(sock.recv(length).decode())

    send("HELLO", {"client_info": "debug-v1"})
    print("HELLO:", recv())

    send("CREATE_SCENE", {"rdla_path": RDLA_PATH})
    print("CREATE_SCENE:", recv())

    send("START_RENDER", {"render_mode": "final"})
    reply = recv()
    print("START_RENDER:", reply)
    stats = reply["payload"]
    w, h, ch = stats["width"], stats["height"], stats["channels"]
    path = "/dev/shm" + stats["shm_name"]
    with open(path, "rb") as f:
        raw = f.read()
    buf = array.array("f")
    buf.frombytes(raw)
    idx = ((h // 2) * w + (w // 2)) * ch
    print("center rgba (rdla-text, bridge04, cube+distant-down) =", buf[idx:idx + 4])
finally:
    proc.terminate()
    proc.wait(timeout=10)
