# Architecture Decision Records

ADRs record consequential, durable technical decisions that would otherwise be easy to rediscover or accidentally reverse.

Current records:

- [`ADR-0001-wsl2-linux-host-boundary.md`](ADR-0001-wsl2-linux-host-boundary.md) — Windows 11 + WSL2/WSLg + Linux Blender as the accepted execution boundary.
- [`ADR-0002-direct-moonray-bridge-primary.md`](ADR-0002-direct-moonray-bridge-primary.md) — Direct Blender ↔ MoonRay Bridge (out-of-process, C++) as the primary integration; Hydra/hdMoonray is reference/fallback only.
- [`ADR-0003-in-process-scene-rdl2-embedding-proposal.md`](ADR-0003-in-process-scene-rdl2-embedding-proposal.md) — **REJECTED.** Re-evaluation of in-process scene_rdl2 embedding via Python bindings; deferred to ADR-0002's own revisit trigger, no architecture change.

Create a new ADR when a change materially affects architecture, ABI boundaries, supported platforms, critical dependencies, compatibility strategy, or reversibility.
