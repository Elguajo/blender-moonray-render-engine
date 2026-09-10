# Phase 04 — Direct MoonRay Bridge prototype and IPC contract

Status: COMPLETE — see `docs/completions/04-direct-bridge-prototype.md`

## Goal
Prove the smallest crash-isolated native bridge that can receive a command from a client, construct/load a minimal MoonRay scene, render, and return status plus image data without Hydra.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Native C++ bridge executable skeleton.
- MoonRay RenderContext lifecycle.
- Local-only control IPC.
- Minimal binary/framebuffer return path.
- Version handshake and structured errors.
- ADR for protocol only if consequential.

## Out of scope
- Full Blender integration.
- Full mesh/material translation.
- Production viewport performance.
- Distributed networking.

## Tasks
- [x] Define minimal versioned message/schema requirements.
- [x] Implement bridge process lifecycle.
- [x] Render a minimal scene through bridge command.
- [x] Return image/status to a test client.
- [x] Test malformed request and bridge restart.
- [x] Measure first basic latency/memory, without optimization claims.

## Acceptance criteria
- [x] Client can start bridge and verify version.
- [x] Bridge renders a known minimal scene through direct MoonRay API.
- [x] Client receives correct image/result without reading a manually exported final file as its only transport.
- [x] Malformed input fails cleanly.
- [x] Bridge process crash/restart does not corrupt client process.

## Negative / failure cases
- Do not expose non-local network listener by default.
- Do not choose a complex serialization framework solely by preference; justify with requirements.

## Verification
- Automated bridge smoke test.
- Golden/known image or deterministic metadata check.
- Exit-code/error-path tests.

## Completion Record
Status: COMPLETE — `docs/completions/04-direct-bridge-prototype.md`, `docs/evidence/phase04/`.
