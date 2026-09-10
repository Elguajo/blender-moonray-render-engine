#!/usr/bin/env python3
"""Phase 04 bridge smoke tests -- docs/phases/04-direct-bridge-prototype.md
"Verification": automated smoke test, golden/deterministic metadata check,
exit-code/error-path tests. Run inside the MoonRay-Rocky9 WSL2 distro after
building the bridge (scripts/linux/phase04_build_bridge.sh).

Exercises every acceptance-criteria bullet against the real bridge binary and
the real MoonRay runtime -- no mocking of the bridge process or MoonRay.
"""
from __future__ import annotations

import array
import json
import os
import socket
import struct
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))
from bridge_client import BridgeClient, BridgeError, read_framebuffer_f32  # noqa: E402

BRIDGE_BIN = os.environ.get("PHASE04_BRIDGE_BIN", "/root/moonray-blender/build/bridge04/moonray_bridge")
RDLA_PATH = os.environ.get(
    "PHASE04_RDLA_PATH", "/root/moonray-blender/src/openmoonray/testdata/rectangle.rdla"
)
LOG_DIR = os.environ.get("PHASE04_LOG_DIR", "/root/moonray-blender/logs/phase04-build")
RDL2_DSO_PATH = os.environ.get(
    "PHASE04_RDL2_DSO_PATH", "/root/moonray-blender/install/openmoonray/rdl2dso"
)

_results = []


def record(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{(' -- ' + detail) if detail else ''}")
    _results.append((name, ok, detail))
    if not ok:
        raise SystemExit(f"PHASE04_TEST_FAILED: {name}: {detail}")


def bridge_env():
    env = dict(os.environ)
    env["RDL2_DSO_PATH"] = RDL2_DSO_PATH
    env["REZ_MOONRAY_ROOT"] = "/root/moonray-blender/install/openmoonray"
    return env


# Defense-in-depth only: a genuine bridge bug during evidence-gathering (a
# dangling RenderOptions& reference, since fixed -- see docs/evidence/phase04/)
# made MoonRay request ~100GB-2TB "allocations" and appeared to destabilize the
# whole WSL2 VM, not just crash the one process. A generous virtual-memory cap
# turns any regression of that class into a clean allocation failure instead.
# 24 GB is comfortably above this test's own observed usage (~1 GB RSS for a
# 512x512 render with 28 threads) and is not a performance-relevant limit.
# Applied via a `bash -c ulimit` wrapper rather than subprocess's preexec_fn:
# the latter forks the Python interpreter itself before exec, which proved
# unreliable under this evidence-gathering session's own sandboxing.
_PHASE04_VMEM_CAP_KB = 24 * 1024 * 1024


def spawn_bridge(socket_path: str, log_path: str):
    proc = subprocess.Popen(
        ["bash", "-c", f'ulimit -v {_PHASE04_VMEM_CAP_KB}; exec "$0" "$@"', BRIDGE_BIN,
         "--socket", socket_path, "--log-dir", LOG_DIR],
        env=bridge_env(),
        stdout=open(log_path, "ab"),
        stderr=subprocess.STDOUT,
    )
    # Startup time is dominated by MoonRay's global driver/thread-pool init and
    # is observed to vary a lot with OS page-cache state (a cold first launch
    # after a fresh build took ~16s in evidence-gathering; a warm re-launch
    # took ~1.2s) -- generous timeout, not a performance claim.
    deadline = time.time() + 40.0
    while time.time() < deadline:
        if os.path.exists(socket_path):
            return proc
        if proc.poll() is not None:
            raise RuntimeError(f"bridge exited early with code {proc.returncode}, see {log_path}")
        time.sleep(0.1)
    proc.kill()
    raise RuntimeError(f"bridge did not create socket {socket_path} within timeout")


def rss_kb(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except (FileNotFoundError, ProcessLookupError):
        return -1
    return -1


def test_version_handshake_ok(socket_path: str):
    with BridgeClient(socket_path) as c:
        reply = c.hello()
        record(
            "handshake: matching protocol_version accepted",
            reply["type"] == "HELLO" and reply["protocol_version"] == 1,
            json.dumps(reply),
        )
        caps = c.capabilities()
        record("capabilities: returns feature list", isinstance(caps["payload"].get("features"), list), json.dumps(caps))


def test_version_mismatch_rejected(socket_path: str):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(socket_path)
    body = json.dumps(
        {"protocol_version": 999, "type": "HELLO", "id": "v1", "payload": {"client_info": "mismatch-test"}}
    ).encode("utf-8")
    sock.sendall(struct.pack("<I", len(body)) + body)
    (length,) = struct.unpack("<I", sock.recv(4))
    reply = json.loads(sock.recv(length).decode("utf-8"))
    record(
        "handshake: version mismatch -> ERROR category 5",
        reply["type"] == "ERROR" and reply["payload"]["category"] == 5 and reply["payload"]["code"] == "VERSION_MISMATCH",
        json.dumps(reply),
    )
    # MESSAGE_SCHEMA.md: version mismatch ends the connection.
    trailing = sock.recv(4)
    record("handshake: connection closed after version mismatch", trailing == b"", repr(trailing))
    sock.close()


def test_render_known_scene(socket_path: str, bridge_pid: int):
    with BridgeClient(socket_path) as c:
        c.hello()
        t0 = time.time()
        scene_ack = c.create_scene(RDLA_PATH)
        record("CREATE_SCENE: accepted known-good rdla", scene_ack["payload"].get("ok") is True, json.dumps(scene_ack))

        render_reply = c.start_render("final")
        t1 = time.time()
        stats = render_reply["payload"]
        record(
            "START_RENDER: RENDER_COMPLETE with expected dimensions",
            stats.get("width") == 512 and stats.get("height") == 512 and stats.get("channels") == 4,
            json.dumps(stats),
        )

        buf = read_framebuffer_f32(stats["shm_name"], stats["width"], stats["height"], stats["channels"])
        lo, hi = min(buf), max(buf)
        has_nan_or_inf = any(v != v or v in (float("inf"), float("-inf")) for v in (lo, hi))
        record(
            "framebuffer: non-constant pixel content, no NaN/Inf in min/max",
            (hi > lo) and not has_nan_or_inf,
            f"min={lo} max={hi}",
        )
        record(
            "framebuffer: read directly from shared memory (not a re-opened export file)",
            os.path.exists("/dev/shm" + stats["shm_name"]),
            stats["shm_name"],
        )

        wall_ms = int((t1 - t0) * 1000)
        rss = rss_kb(bridge_pid)
        print(f"[INFO] latency: CREATE_SCENE+START_RENDER round trip = {wall_ms} ms (client-observed, unoptimized)")
        print(f"[INFO] memory: bridge process RSS after render = {rss} kB (unoptimized, single small scene)")


def test_malformed_input(socket_path: str):
    with BridgeClient(socket_path) as c:
        c.hello()

        # Well-framed but invalid JSON body.
        c._send_raw(b"{not json")
        reply = c.recv()
        record(
            "malformed: invalid JSON -> ERROR category 1, connection stays open",
            reply["type"] == "ERROR" and reply["payload"]["category"] == 1,
            json.dumps(reply),
        )

        # Well-formed envelope, unknown message type.
        c._send_raw(json.dumps({"protocol_version": 1, "type": "NOT_A_REAL_TYPE", "id": "m1", "payload": {}}).encode())
        reply = c.recv()
        record(
            "malformed: unknown type -> ERROR (hard error, not silently ignored)",
            reply["type"] == "ERROR" and reply["payload"]["code"] == "UNKNOWN_MESSAGE_TYPE",
            json.dumps(reply),
        )

        # CREATE_SCENE with a nonexistent path -- category 1 validation error,
        # must fail before touching native RDL2 state.
        try:
            c.create_scene("/nonexistent/path/does-not-exist.rdla")
            record("malformed: nonexistent rdla_path rejected", False, "did not raise")
        except BridgeError as e:
            record(
                "malformed: nonexistent rdla_path -> ERROR category 1",
                e.category == 1,
                str(e),
            )

        # Connection must still be usable after all of the above.
        caps = c.capabilities()
        record("malformed: connection still usable after errors", caps["type"] == "CAPABILITIES", json.dumps(caps))


def test_crash_restart(base_socket_dir: str):
    socket_path = os.path.join(base_socket_dir, "crash.sock")
    log_path = os.path.join(LOG_DIR, "bridge-crash-test.log")
    proc = spawn_bridge(socket_path, log_path)
    try:
        with BridgeClient(socket_path) as c:
            c.hello()
            c.create_scene(RDLA_PATH)

            proc.kill()  # SIGKILL: simulate an unrecoverable bridge crash
            proc.wait(timeout=5.0)

            crashed_cleanly = False
            try:
                c.start_render("final")
            except (ConnectionError, BrokenPipeError, OSError):
                crashed_cleanly = True
            record(
                "crash: client observes a clean connection failure, not a hang/exception storm",
                crashed_cleanly,
                "",
            )
    finally:
        if proc.poll() is None:
            proc.kill()

    # A fresh bridge process on a fresh socket must work normally --
    # "Bridge process crash/restart does not corrupt client process."
    socket_path2 = os.path.join(base_socket_dir, "restart.sock")
    log_path2 = os.path.join(LOG_DIR, "bridge-restart-test.log")
    proc2 = spawn_bridge(socket_path2, log_path2)
    try:
        with BridgeClient(socket_path2) as c:
            reply = c.hello()
            record(
                "restart: fresh bridge process after a crash handles a new session normally",
                reply["type"] == "HELLO",
                json.dumps(reply),
            )
    finally:
        proc2.terminate()
        proc2.wait(timeout=5.0)


def main():
    workdir = os.environ.get("PHASE04_RUNTIME_DIR", "/tmp/phase04-bridge-tests")
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    main_socket = os.path.join(workdir, "main.sock")
    main_log = os.path.join(LOG_DIR, "bridge-main.log")
    proc = spawn_bridge(main_socket, main_log)
    try:
        test_version_handshake_ok(main_socket)
        test_version_mismatch_rejected(main_socket)
        test_render_known_scene(main_socket, proc.pid)
        test_malformed_input(main_socket)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()

    test_crash_restart(workdir)

    print(f"\nPHASE04_TESTS_OK -- {len(_results)} checks passed")


if __name__ == "__main__":
    main()
