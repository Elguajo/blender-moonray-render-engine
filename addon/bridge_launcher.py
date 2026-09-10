"""Launches, version-checks and tears down one moonray_bridge process per
render (docs/bridge/LIFECYCLE.md "Bridge process lifecycle": "launched and
version-checked by the Blender integration ... does not self-register or run
as a persistent background service by default").

Phase 05 launches a fresh bridge per F12 render and shuts it down afterward
(one-shot, matching Phase 04's "one client connection at a time" bridge and
this phase's synchronous-batch-only scope) rather than keeping a long-lived
bridge process across renders -- persistent-bridge lifecycle/restart policy
is Phase 11 scope (docs/bridge/LIFECYCLE.md "Auto-restart/backoff policy
after crash" -- Open).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
import uuid

from . import bridge_client

# Phase 06 build output (scripts/linux/phase06_build_bridge.sh, protocol_version
# 2 -- structured CREATE_SCENE/UPDATE_OBJECT/UPDATE_CAMERA). The build
# directory is disposable/not committed -- overridable via the add-on's
# "Bridge Binary" preference for a rebuilt or relocated binary.
DEFAULT_BRIDGE_BIN = "/root/moonray-blender/build/bridge06/moonray_bridge"
DEFAULT_RDL2_DSO_PATH = "/root/moonray-blender/install/openmoonray/rdl2dso"
DEFAULT_REZ_MOONRAY_ROOT = "/root/moonray-blender/install/openmoonray"

# Phase 04 evidence: cold start after a fresh build took ~16s (MoonRay global
# driver/thread-pool init), a warm relaunch ~1.2s -- generous, not a
# performance claim (docs/evidence/phase04/).
STARTUP_TIMEOUT_S = 40.0


class BridgeLaunchError(RuntimeError):
    """The bridge process could not be started or would not complete its
    HELLO handshake. Mirrors ERROR_MODEL.md category 4/5 handling on the
    add-on side."""


class BridgeHandle:
    """One running moonray_bridge process plus its connected control client."""

    def __init__(self, process: subprocess.Popen, client: bridge_client.BridgeClient, socket_path: str, log_path: str):
        self.process = process
        self.client = client
        self.socket_path = socket_path
        self.log_path = log_path

    def is_alive(self) -> bool:
        return self.process.poll() is None

    def shutdown(self) -> None:
        """Always safe to call, any number of times, regardless of whether
        the process already exited on its own (crash) -- this is what
        guarantees a cancelled or failed render never leaves a zombie bridge
        process (docs/phases/05-blender-renderengine-integration.md
        acceptance: "Cancel does not leave zombie bridge/render")."""
        try:
            self.client.close()
        except Exception:
            pass
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                try:
                    self.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    pass
        try:
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except OSError:
            pass


def launch_and_connect(bridge_bin: str = "", log_dir: str = "") -> BridgeHandle:
    """Starts moonray_bridge, waits for its socket, connects, and completes
    the HELLO handshake. Raises BridgeLaunchError on any failure along the
    way -- callers must not proceed to CREATE_SCENE/START_RENDER without a
    successful return here."""
    bridge_bin = bridge_bin or DEFAULT_BRIDGE_BIN
    if not os.path.isfile(bridge_bin) or not os.access(bridge_bin, os.X_OK):
        raise BridgeLaunchError(
            f"moonray_bridge binary not found or not executable: {bridge_bin!r} "
            "(build it with scripts/linux/phase04_build_bridge.sh, or set the "
            "add-on's Bridge Binary path in Render Properties)"
        )

    run_dir = log_dir or tempfile.mkdtemp(prefix="moonray_blender_")
    os.makedirs(run_dir, exist_ok=True)
    socket_path = os.path.join(run_dir, f"bridge_{uuid.uuid4().hex[:8]}.sock")
    stdout_path = os.path.join(run_dir, "moonray_bridge.stdout.log")

    env = dict(os.environ)
    env["RDL2_DSO_PATH"] = DEFAULT_RDL2_DSO_PATH
    env["REZ_MOONRAY_ROOT"] = DEFAULT_REZ_MOONRAY_ROOT

    process = subprocess.Popen(
        [bridge_bin, "--socket", socket_path, "--log-dir", run_dir],
        env=env,
        stdout=open(stdout_path, "ab"),
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + STARTUP_TIMEOUT_S
    while time.time() < deadline:
        if os.path.exists(socket_path):
            break
        if process.poll() is not None:
            raise BridgeLaunchError(
                f"moonray_bridge exited during startup (exit code {process.returncode}); see {stdout_path}"
            )
        time.sleep(0.1)
    else:
        process.kill()
        raise BridgeLaunchError(f"moonray_bridge did not create its socket within {STARTUP_TIMEOUT_S}s; see {stdout_path}")

    try:
        client = bridge_client.BridgeClient(socket_path)
        client.hello()
    except Exception as exc:
        process.kill()
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            pass
        raise BridgeLaunchError(f"HELLO handshake with moonray_bridge failed: {exc}") from exc

    return BridgeHandle(process, client, socket_path, stdout_path)
