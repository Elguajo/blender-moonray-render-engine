# ADR-0004 — Bridge IPC transport, wire format and bulk-data path (Phase 04)

Status: ACCEPTED
Date: 2026-09-10
Relates to: ADR-0002 (out-of-process bridge boundary — this ADR fills in the
mechanics ADR-0002 deliberately left open), `docs/bridge/PROTOCOL.md`

## Context
ADR-0002 decided that `moonray_bridge` is a separate native process, but
explicitly left the exact IPC mechanism, wire encoding and bulk-data transport
open, to be "selected and benchmarked during implementation"
(`docs/project/ARCHITECTURE.md`) rather than picked by preference. Phase 04
(`docs/phases/04-direct-bridge-prototype.md`) is that implementation: "prove
the smallest crash-isolated native bridge that can receive a command from a
client, construct/load a minimal MoonRay scene, render, and return status plus
image data without Hydra." `docs/bridge/PROTOCOL.md`'s "Decided vs. open"
table listed four items as Phase-04-owned: exact wire format, exact IPC
mechanism, bulk-payload reference format, and framebuffer pixel/channel
layout. This ADR records those four decisions together because they are one
coherent transport design, evidenced by a working prototype rather than
argued from first principles.

## Decision

### Control-plane transport: Unix domain socket
`AF_UNIX`/`SOCK_STREAM`, bound to a filesystem path, one client connection at
a time. Local-only by construction (no `AF_INET` listener exists in the code
at all — satisfies ADR-0002/ARCHITECTURE.md "no non-local network listener by
default" without relying on a runtime flag to disable one). A named pipe or
gRPC-over-UDS were the documented alternatives (`PROTOCOL.md`); a plain UDS
was chosen because Phase 04's actual requirement — the add-on, and only the
add-on, talks to one bridge process it launched itself — needs nothing a
richer transport would add, and every extra dependency has to be justified
under `docs/phases/04-direct-bridge-prototype.md`'s own negative constraint
("do not choose a complex serialization framework solely by preference").

### Wire encoding: JSON, length-prefixed, via JsonCpp
Every control-plane message is a 4-byte little-endian length prefix followed
by that many bytes of a JSON object matching the envelope in
`docs/bridge/MESSAGE_SCHEMA.md` (`protocol_version`/`type`/`id`/`payload`).
JsonCpp was selected as the encoder/decoder not by preference but because it
is **already a transitive third-party dependency of the pinned Phase 03
MoonRay/scene_rdl2 build** — `SceneRdl2Config.cmake` itself calls
`find_dependency(JsonCpp)`, and `/opt/MoonRay/installs/lib64/libjsoncpp.so`
already exists from the Phase 03 dependency build (see
`docs/evidence/phase04/build-configure-summary.txt`). Choosing it adds zero
new build/runtime dependencies to the project. A binary framing technology
(protobuf/Cap'n Proto/FlatBuffers) was rejected for this prototype: Phase 04's
own message volume (a handful of control messages per render) does not need
one, and `MESSAGE_SCHEMA.md` was written precisely so a later switch changes
only the encoding of the same envelope/message-type contract, not the
contract itself, should Phase 08/10 benchmarking show JSON parsing overhead
matters for progressive-viewport control-message rates.

### Bulk transport: POSIX shared memory, one named segment per render
Beauty-buffer pixel data never travels through the JSON envelope. Instead the
bridge publishes it into a freshly created, uniquely named POSIX shared-memory
segment (`shm_open`+`ftruncate`+`mmap`+`memcpy`+`munmap`, per
`bridge/src/SharedMemoryBuffer.cpp`) and the control-plane `RENDER_COMPLETE`
message carries only a reference: `shm_name`, `width`, `height`, `channels`,
`dtype`, `byte_size`. This was chosen over a binary socket stream or a mapped
file because MoonRay's own `RenderContext::snapshotRenderBuffer()` already
produces one contiguous `fb_util::RenderBuffer` (`PixelBuffer<Vec4f>`) — bulk
publication is therefore a single `memcpy` with no serialization step, and the
client reads it back with a single file read from `/dev/shm<name>` (POSIX shm
segments are backed by tmpfs there on Linux), with no ring-buffer/backpressure
machinery needed yet since Phase 04 has exactly one render in flight at a
time. Ring-buffer or streaming delivery for progressive viewport updates
remains explicitly open for Phase 08/10, per `docs/bridge/FRAMEBUFFER_PROTOCOL.md`.

### Pixel layout: interleaved RGBA float32
This is not an independent choice — it is RDL2's own native in-memory layout
for `fb_util::RenderBuffer` (`typedef PixelBuffer<RenderColor> RenderBuffer;`
`RenderColor = math::Vec4f`). Publishing it as-is (no planar repacking, no
half-float downconversion) keeps the bridge's bulk path a pure `memcpy` in
both directions and avoids inventing a new on-wire pixel format ahead of any
requirement (AOV-specific formats are Phase 09 scope).

## Evidence
`docs/evidence/phase04/` — full build log excerpt, full smoke-test run (14/14
checks: version handshake including a rejected version mismatch, capabilities
query, a real `CREATE_SCENE`+`START_RENDER` against the same
`testdata/rectangle.rdla` scene Phase 03 proved renders, a live shared-memory
framebuffer read with non-constant/no-NaN pixel content, four distinct
malformed-input cases each producing a clean structured `ERROR` without
corrupting the connection, and a real `SIGKILL` crash + fresh-process restart
both observed to behave correctly from the client's side).

## Consequences
### Positive
- Zero new third-party dependencies (JsonCpp already built by Phase 03;
  POSIX shared memory and Unix domain sockets are libc/kernel facilities).
- The message-level contract (`MESSAGE_SCHEMA.md`) and its wire encoding stay
  cleanly separated, exactly as that document was designed to allow — a later
  encoding change does not require redesigning what the two sides say to each
  other.
- Bulk transport is a `memcpy` in, a single read in, with no manual
  per-pixel/per-element loop on either side (satisfies ADR-0002/ARCHITECTURE.md's
  bulk-transport principle).

### Costs / open follow-ups
- One client connection at a time is a Phase 04 simplification; concurrent or
  reconnecting-client semantics are not yet designed (not needed until a real
  multi-consumer use case appears — none is scoped before Phase 11).
  There is also no `--socket`-path collision guard between two bridge
  instances; the launcher (Phase 05's Blender add-on) is presumed to own
  socket-path uniqueness, matching `PosixSocketServer`'s own documented
  assumption.
- Shared-memory segment cleanup is session-scoped (the bridge unlinks the
  previous render's segment when starting the next, and on clean shutdown);
  a client that never disconnects cleanly could theoretically leak one
  trailing segment per crashed session. Acceptable for a prototype; revisit
  under Phase 11 (stability/recovery/packaging) if it proves material.
- JSON parsing cost on the control plane is unmeasured against a progressive-
  viewport message rate (many small updates per second) — Phase 08/10's own
  benchmark work owns that question; this ADR only claims JSON is adequate
  for Phase 04's message volume (one-shot batch render), not that it will
  remain the right choice at viewport-frequency control traffic.

## Revisit triggers
- Phase 08/10 benchmark evidence shows JSON control-plane parsing is a
  measured bottleneck at progressive-viewport message rates.
- A real requirement for concurrent bridge clients emerges.
- Phase 11 stability work finds the shared-memory cleanup policy above
  insufficient in practice.
