"""Production Blender add-on client for moonray_bridge.

Implements the same wire contract as bridge/client/bridge_client.py (the
Phase 04 test client this module is modeled on, per NEXT_SESSION.md's
"reference Python-client protocol / template for the add-on's own client"):
a 4-byte little-endian length prefix followed by a JSON envelope
{protocol_version, type, id, payload} (docs/bridge/MESSAGE_SCHEMA.md).

This copy is intentionally separate from bridge/client/bridge_client.py: the
add-on must be self-contained (installable as its own zip) and must not
depend on files outside addon/, and it drops the Phase-04-test-only
_send_raw() malformed-input hook this module has no use for.
"""
from __future__ import annotations

import array
import itertools
import json
import os
import socket
import struct
from dataclasses import dataclass, field
from typing import Any, Optional

PROTOCOL_VERSION = 2
MAX_MESSAGE_BYTES = 16 * 1024 * 1024


class BridgeError(Exception):
    def __init__(self, category: int, code: str, message: str):
        super().__init__(f"[category {category}] {code}: {message}")
        self.category = category
        self.code = code
        self.message = message


@dataclass
class Envelope:
    type: str
    id: str
    payload: dict = field(default_factory=dict)
    protocol_version: int = PROTOCOL_VERSION


class BridgeClient:
    def __init__(self, socket_path: str, connect_timeout: float = 5.0):
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.settimeout(connect_timeout)
        self._sock.connect(socket_path)
        # `settimeout` above bounds only the connect() call above it, not
        # the lifetime of the socket -- a Python socket timeout, once set,
        # otherwise applies to every future send/recv too. START_RENDER's
        # response can legitimately take much longer than a short connect
        # timeout (observed: several seconds at low resolution/samples,
        # longer at higher settings) since it blocks for the full synchronous
        # MoonRay render (bridge/src/RenderSession.cpp: one BATCH render per
        # START_RENDER, no streaming/incremental replies in Phase 04/05).
        # Reverting to blocking (no timeout) after connect avoids
        # mistranslating "still rendering" into a false ConnectionError/OSError
        # (this was reproduced end-to-end: a real GUI render surfaced as
        # "MoonRay: bridge connection lost (process crash?): timed out" purely
        # from this leftover 5s timeout, not an actual bridge crash -- see
        # docs/evidence/phase05/).
        self._sock.settimeout(None)
        self._ids = itertools.count(1)

    def close(self):
        try:
            self._sock.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _next_id(self) -> str:
        return f"addon{next(self._ids)}"

    def _send(self, env: Envelope) -> None:
        body = json.dumps(
            {
                "protocol_version": env.protocol_version,
                "type": env.type,
                "id": env.id,
                "payload": env.payload,
            }
        ).encode("utf-8")
        self._sock.sendall(struct.pack("<I", len(body)) + body)

    def _recv_exact(self, n: int) -> bytes:
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = self._sock.recv(remaining)
            if not chunk:
                raise ConnectionError("peer closed connection while a frame was expected")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def recv(self) -> dict:
        (length,) = struct.unpack("<I", self._recv_exact(4))
        if length == 0 or length > MAX_MESSAGE_BYTES:
            raise ValueError(f"bridge sent an out-of-bounds frame length: {length}")
        body = self._recv_exact(length)
        return json.loads(body.decode("utf-8"))

    def request(self, type_: str, payload: Optional[dict] = None) -> dict:
        env = Envelope(type=type_, id=self._next_id(), payload=payload or {})
        self._send(env)
        reply = self.recv()
        if reply["type"] == "ERROR":
            p = reply["payload"]
            raise BridgeError(p.get("category", 0), p.get("code", ""), p.get("message", ""))
        return reply

    def hello(self, client_info: str = "blender-moonray-addon") -> dict:
        reply = self.request("HELLO", {"client_info": client_info})
        if reply.get("protocol_version") != PROTOCOL_VERSION:
            raise BridgeError(
                5,
                "VERSION_MISMATCH",
                f"add-on speaks protocol_version {PROTOCOL_VERSION}, bridge replied {reply.get('protocol_version')}",
            )
        return reply

    def capabilities(self) -> dict:
        return self.request("CAPABILITIES")

    def create_scene(self, scene_variables: Optional[dict] = None) -> dict:
        return self.request("CREATE_SCENE", {"scene_variables": scene_variables or {}})

    def update_object(self, payload: dict) -> dict:
        return self.request("UPDATE_OBJECT", payload)

    def update_camera(self, payload: dict) -> dict:
        return self.request("UPDATE_CAMERA", payload)

    def start_render(self, render_mode: str = "final") -> dict:
        return self.request("START_RENDER", {"render_mode": render_mode})


def read_framebuffer_f32(shm_name: str, width: int, height: int, channels: int = 4) -> array.array:
    """Reads an RGBA float32 framebuffer published via POSIX shared memory.

    POSIX shm segments are backed by /dev/shm on Linux (the add-on only ever
    runs inside the WSL2 Linux boundary alongside the bridge, per ADR-0001),
    so a plain file read is sufficient.
    """
    path = "/dev/shm" + shm_name if not shm_name.startswith("/dev/shm") else shm_name
    expected_bytes = width * height * channels * 4
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) != expected_bytes:
        raise ValueError(f"shared memory segment {shm_name} has {len(raw)} bytes, expected {expected_bytes}")
    buf = array.array("f")
    buf.frombytes(raw)
    return buf
