# Bridge Protocol — Overview

Status: **TARGET DESIGN, not an implementation claim.** No bridge process exists yet
(Roadmap Phase 04 — `docs/phases/04-direct-bridge-prototype.md` — is not started).
This directory formalizes the contract sketched in
[`docs/design/DIRECT_BRIDGE_TARGET.md`](../design/DIRECT_BRIDGE_TARGET.md) and will be
tightened with evidence as Phases 04/06/07/08/09/11 land. Where this document and
`docs/project/ARCHITECTURE.md` disagree, ARCHITECTURE.md wins.

## Sources of truth
- Product/process boundary → `docs/project/ARCHITECTURE.md`
- Why out-of-process / why direct → `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md`
- Phase scope/acceptance → `docs/phases/04-direct-bridge-prototype.md` and later phases
- RDL2 object/attribute model → `docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md`

## Documents in this contract
| Document | Covers |
|---|---|
| [MESSAGE_SCHEMA.md](MESSAGE_SCHEMA.md) | Message envelope, `protocol_version` handshake, fixed message-type enum |
| [SCENE_TRANSLATION.md](SCENE_TRANSLATION.md) | Blender data → bridge scene messages → RDL2 `SceneObject`s |
| [FRAMEBUFFER_PROTOCOL.md](FRAMEBUFFER_PROTOCOL.md) | Progressive/final beauty and AOV snapshot delivery back to Blender |
| [ERROR_MODEL.md](ERROR_MODEL.md) | Validation failures, native render errors, crash/restart signaling |
| [LIFECYCLE.md](LIFECYCLE.md) | Bridge process, scene-session and render-mode state machines |

## Process boundary (decided — ADR-0002)
```text
Blender add-on                     moonray_bridge (native process)
──────────────                     ─────────────────────────────
RenderEngine          control IPC  RenderContext / SceneContext
Depsgraph        ───────────────▶  incremental RDL2 updates
Settings         ◀───────────────  version/status/errors
Viewport              bulk data    progressive framebuffer/AOVs
               ◀═════════════════  binary/shared-memory transport
```
- Blender add-on and `moonray_bridge` are separate OS processes (crash/ABI isolation).
- Small control/status/settings messages travel over local IPC.
- Bulk geometry/framebuffer/AOV payloads travel over an efficient binary or shared-memory
  path — never a Python per-element loop.
- No non-local network listener by default; bridge is a localhost/Unix-socket peer only.
- Bridge treats every incoming message as untrusted input, even though the add-on is
  normally its only client.

## Decided vs. open
| Aspect | Status |
|---|---|
| Two-process boundary (add-on ↔ native bridge) | **Decided** — ADR-0002 |
| Control-plane messages use local IPC, bulk-plane uses binary/shared memory | **Decided** — ARCHITECTURE.md data-plane principle |
| Bridge is launched and version-checked by the Blender integration | **Decided** — ARCHITECTURE.md operational assumptions |
| Exact wire format / serialization technology (protobuf, Cap'n Proto, FlatBuffers, custom) | **Open — Phase 04.** Do not pre-select without measured requirements. |
| Exact IPC mechanism (Unix domain socket, named pipe, gRPC-over-UDS, etc.) | **Open — Phase 04** |
| Message envelope, fixed message-type enum, `protocol_version` handshake | **Decided (shape) — see [MESSAGE_SCHEMA.md](MESSAGE_SCHEMA.md).** Wire encoding of that same contract stays Open — Phase 04. |
| Full-scene sync vs. incremental sync as the first milestone | **Decided for M0** — full-scene sync acceptable for first F12; incremental becomes mandatory before viewport production acceptance (DIRECT_BRIDGE_TARGET.md rule 6). Exact incremental-update wire semantics are **Open — Phase 06**. |

## Non-goals (current contract)
- Distributed/network rendering (Arras) — out of scope per Phase 04/11.
- In-process (single-process) MoonRay integration — rejected for now per ADR-0002; revisit
  only under a new ADR if Phase 10 benchmark evidence demands it.
- Full Blender node-graph / Cycles shader parity — bounded per Phase 07 support matrix.
