# Architecture Decision Records

ADRs record consequential, durable technical decisions that would otherwise be easy to rediscover or accidentally reverse.

Current records:

- [`ADR-0001-wsl2-linux-host-boundary.md`](ADR-0001-wsl2-linux-host-boundary.md) — Windows 11 + WSL2/WSLg + Linux Blender as the accepted execution boundary.
- [`ADR-0002-direct-moonray-bridge-primary.md`](ADR-0002-direct-moonray-bridge-primary.md) — Direct Blender ↔ MoonRay Bridge (out-of-process, C++) as the primary integration; Hydra/hdMoonray is reference/fallback only.
- [`ADR-0003-in-process-scene-rdl2-embedding-proposal.md`](ADR-0003-in-process-scene-rdl2-embedding-proposal.md) — **REJECTED.** Re-evaluation of in-process scene_rdl2 embedding via Python bindings; deferred to ADR-0002's own revisit trigger, no architecture change.
- [`ADR-0004-bridge-ipc-transport-and-wire-format.md`](ADR-0004-bridge-ipc-transport-and-wire-format.md) — Bridge control-plane transport (Unix domain socket, JSON/JsonCpp) and bulk-data transport (POSIX shared memory, interleaved RGBA float32) for the Phase 04 prototype.
- [`ADR-0005-structured-scene-protocol.md`](ADR-0005-structured-scene-protocol.md) — Structured `CREATE_SCENE`/`UPDATE_OBJECT`/`UPDATE_CAMERA` protocol (native RDL2 `SceneObject` construction in the bridge) replaces Phase 04/05's raw `.rdla`-path `CREATE_SCENE`; `protocol_version` 1 → 2.

Create a new ADR when a change materially affects architecture, ABI boundaries, supported platforms, critical dependencies, compatibility strategy, or reversibility.
