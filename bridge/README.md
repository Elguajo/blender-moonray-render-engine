# `bridge/`

The native `moonray_bridge` process: a separate local C++ process hosting
MoonRay/scene_rdl2 and exposing a versioned local control + bulk-data
boundary to Blender, per ADR-0002 (out-of-process boundary) and ADR-0004
(IPC transport/wire format).

Phase 04 (`docs/phases/04-direct-bridge-prototype.md`,
`docs/completions/04-direct-bridge-prototype.md`) implemented and evidenced
the prototype: version handshake, a full-scene `.rdla` load through the
direct MoonRay `RenderContext` API, one synchronous batch render, and
framebuffer delivery over POSIX shared memory. Full Blender integration
(Phase 05), incremental scene updates (Phase 06+), and progressive viewport
delivery (Phase 08) are not yet implemented.

## Layout
- `src/` — the `moonray_bridge` executable source (see file-level comments
  for each module's responsibility).
- `client/bridge_client.py` — a minimal test client implementing the wire
  protocol (`docs/bridge/MESSAGE_SCHEMA.md`); not the production Blender
  add-on client.
- `tests/run_phase04_tests.py` — the Phase 04 automated smoke test.

## Building
`scripts/linux/phase04_build_bridge.sh` (run inside the `MoonRay-Rocky9` WSL2
distro, against the Phase 03 installed runtime). The build directory itself
must stay on the Linux-native filesystem, never under `/mnt/*` — only the
source is read from the Windows-mounted repo path.
