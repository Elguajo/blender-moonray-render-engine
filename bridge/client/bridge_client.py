"""Minimal Phase 04 test client for moonray_bridge.

Not the production Blender add-on client (that is Phase 05+ scope) -- this is
the "test client" referenced by docs/phases/04-direct-bridge-prototype.md
acceptance criteria ("Client can start bridge and verify version", "Client
receives correct image/result"). Implements exactly the wire contract in
docs/bridge/MESSAGE_SCHEMA.md: a 4-byte little-endian length prefix followed
by a JSON envelope {protocol_version, type, id, payload}.

Framebuffer reads use Python's `array` module (a single C-level frombytes()
call, not a per-pixel Python loop) to stay consistent with the project's bulk
data constraints even in this best-effort test tool.
"""
from __future__ import annotations

import array
import json
import os
import socket
import struct
import itertools
from dataclasses import dataclass, field
from typing import Any, Optional

PROTOCOL_VERSION = 1
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
        self._ids = itertools.count(1)

    def close(self):
        self._sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _next_id(self) -> str:
        return f"c{next(self._ids)}"

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

    def _send_raw(self, raw_body: bytes) -> None:
        """For malformed-input tests: bypass envelope construction entirely."""
        self._sock.sendall(struct.pack("<I", len(raw_body)) + raw_body)

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

    def hello(self, client_info: str = "phase04-test-client") -> dict:
        return self.request("HELLO", {"client_info": client_info})

    def capabilities(self) -> dict:
        return self.request("CAPABILITIES")

    def create_scene(self, rdla_path: str) -> dict:
        return self.request("CREATE_SCENE", {"rdla_path": rdla_path})

    def start_render(self, render_mode: str = "final") -> dict:
        return self.request("START_RENDER", {"render_mode": render_mode})


def read_framebuffer_f32(shm_name: str, width: int, height: int, channels: int = 4) -> array.array:
    """Reads an RGBA float32 framebuffer published via POSIX shared memory.

    POSIX shm segments are backed by /dev/shm on Linux, so a plain file read
    is sufficient -- no ctypes/mmap module needed for this test client.
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
