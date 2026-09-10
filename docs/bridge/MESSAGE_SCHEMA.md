# Message Schema & Versioning

Status: **TARGET DESIGN, not an implementation claim.** See [PROTOCOL.md](PROTOCOL.md) for
status conventions. Authoritative acceptance criteria live in
`docs/phases/04-direct-bridge-prototype.md` ("Define minimal versioned message/schema
requirements", "Client can start bridge and verify version").

## What this covers
The control-plane message envelope, the fixed message-type set, and the versioning/handshake
rule that let the add-on and `moonray_bridge` reject an incompatible peer *before* any scene
or framebuffer data is exchanged. This document does not fix wire encoding (JSON vs.
FlatBuffers vs. Cap'n Proto vs. shared memory — **Open, Phase 04**, per
[PROTOCOL.md](PROTOCOL.md) "Decided vs. open"), and it does not fix the per-object attribute
field layout for meshes/cameras/materials (owned by [SCENE_TRANSLATION.md](SCENE_TRANSLATION.md)).
It exists so that whichever encoding Phase 04 picks first, the add-on and bridge already agree
on *what a message is allowed to be*, instead of passing an arbitrary Python `dict`/JSON blob
with no contract.

## Why an explicit contract instead of ad hoc dict/JSON
- [ERROR_MODEL.md](ERROR_MODEL.md) category 1 requires payload validation *before* any native
  RDL2 mutation. That is only checkable if every message has a declared shape.
- [ERROR_MODEL.md](ERROR_MODEL.md) category 5 requires detecting an incompatible
  protocol/build *before* scene/framebuffer data is exchanged — impossible without a
  versioned handshake that happens first, unconditionally.
- The bridge treats all input as untrusted by design (`docs/project/ARCHITECTURE.md`
  security/trust boundaries) even though the add-on is normally its only client. Untrusted
  input needs a schema to be validated against, not "whatever Python happened to serialize".
- Swapping transport later (DIRECT_BRIDGE_TARGET.md rule 7/8, PROTOCOL.md "exact wire format
  — Open") must not force a redesign of *what* the two sides say to each other, only *how*
  bytes carry it. That separation only holds if the message set is defined independently of
  encoding now.

## Envelope (decided shape)
Every control-plane message — regardless of encoding — carries the same four fields:

```text
protocol_version : int      # negotiated wire contract version (see below)
type             : enum     # one of the fixed message types below
id               : string   # correlates a request to its response/ERROR; opaque, sender-assigned
payload          : object   # type-specific fields; see "Message set" below
```

`id` is present on every request-shaped message (`CREATE_SCENE`, `UPDATE_OBJECT`,
`UPDATE_CAMERA`, `UPDATE_MATERIAL`, `START_RENDER`, `STOP_RENDER`) and echoed back by any
`ERROR` or acknowledgement that resulted from it, so a client can tell *which* in-flight
request failed. `HELLO`/`CAPABILITIES` use `id` only for their own request/response pairing.
`FRAME_UPDATE`/`RENDER_COMPLETE` are bridge-initiated and correlate to the `id` of the
`START_RENDER` they belong to, not to themselves.

A message whose `type` is not in the fixed set below, or whose `payload` fails validation for
the negotiated `protocol_version`, is rejected with `ERROR` and must not reach RDL2/MoonRay
state — this is the wire-level expression of ERROR_MODEL category 1.

## Versioning rule (decided)
`protocol_version` is a single monotonically increasing integer (`1`, `2`, ...) identifying the
envelope shape and message-type semantics — **not** a build/release version of the add-on or
bridge binary, and **not** SemVer. SemVer is rejected here: the add-on and `moonray_bridge` are
developed and shipped together out of the same repository, so there is no independent-vendor
compatibility range to express — only "does this pair of processes agree on one integer".

- **Breaking change** (removes/renames a field, changes a field's type or semantics, removes a
  message type, changes what a message type means) → bump `protocol_version`.
- **Additive change** (new optional field, new message type, new `CAPABILITIES` flag) → does
  **not** require a bump. Receivers must ignore unknown fields inside an otherwise-known
  message (forward compatibility) but must treat an unknown `type` as a hard error, never
  silently ignore it (ERROR_MODEL: unsupported must be explicit, never silent).
- A single bridge/add-on build advertises exactly one `protocol_version` in Phase 04 (no
  negotiation range needed yet: both sides are versioned together). Supporting a *range* of
  `protocol_version`s in one build is **Open** and only worth adding once independent
  upgrade of add-on vs. bridge binary is a real deployment case (not before Phase 11
  packaging).

## Handshake (decided shape)
```text
add-on                                    moonray_bridge
  │                                              │
  ├── connect (transport-level) ────────────────▶│
  │                                              │
  ├── HELLO{protocol_version, client_info} ─────▶│
  │                                              │  version check
  │◀───────────── HELLO{protocol_version, bridge_info}  (match)
  │◀───────────── ERROR{VERSION_MISMATCH}              (no match) — connection ends
  │                                              │
  ├── CAPABILITIES{} (query) ───────────────────▶│
  │◀───────────── CAPABILITIES{features: [...]} ─┤
  │                                              │
  │        ... CREATE_SCENE / UPDATE_* / START_RENDER now permitted ...
```
- `HELLO` is always the first message on a new connection, in both directions; any other
  message type sent before a successful `HELLO` exchange is a protocol error.
- `HELLO` failing on version mismatch ends the connection without attempting scene or
  framebuffer exchange — this is what makes ERROR_MODEL category 5 detectable up front rather
  than as a confusing failure mid-`CREATE_SCENE`.
- `CAPABILITIES` is separate from `HELLO` because capabilities are a growing, additive set
  (which AOVs are registered, whether shared-memory framebuffer delivery is available,
  whether incremental scene updates are supported) that must not force a `protocol_version`
  bump every time a feature is added — see FRAMEBUFFER_PROTOCOL.md's "AOV registration
  handshake" and LIFECYCLE.md's per-attribute update-pause classification, both of which are
  natural `CAPABILITIES` entries once their owning phase defines them. The exact flag
  vocabulary is **Open**, populated incrementally by Phase 04/08/09 as each feature exists to
  advertise.
- `CREATE_SCENE`/`UPDATE_*`/`START_RENDER` sent before a successful handshake are rejected
  with `ERROR`, never processed "optimistically".

## Message set (decided: fixed enum; payload field layout mostly open)

| Type | Direction | Correlates via `id` | Payload status |
|---|---|---|---|
| `HELLO` | bidirectional, first on connection | own request/response | Decided: `protocol_version`, opaque `client_info`/`bridge_info` string |
| `CAPABILITIES` | bidirectional, after `HELLO` | own request/response | Open — flag vocabulary grows per phase (see above) |
| `CREATE_SCENE` | add-on → bridge | request → ack/`ERROR` | **Decided and implemented — Phase 06**: `payload.scene_variables` (`image_width`/`image_height`/`pixel_samples`); see [SCENE_TRANSLATION.md](SCENE_TRANSLATION.md) |
| `UPDATE_OBJECT` | add-on → bridge | request → ack/`ERROR` | **Decided and implemented — Phase 06** (geometry/transform/light; camera and material split out below): `payload.op` (`create`/`update`/`delete`), `payload.kind` (`mesh`/`light`), `payload.name`, plus kind-specific fields — see [SCENE_TRANSLATION.md](SCENE_TRANSLATION.md) |
| `UPDATE_CAMERA` | add-on → bridge | request → ack/`ERROR` | **Decided and implemented — Phase 06**, see SCENE_TRANSLATION.md "Camera" |
| `UPDATE_MATERIAL` | add-on → bridge | request → ack/`ERROR` | Open — Phase 07, see SCENE_TRANSLATION.md "Materials" |
| `START_RENDER` | add-on → bridge | request → ack, then streamed `FRAME_UPDATE`/`RENDER_COMPLETE` | Decided: `render_mode` (`viewport`/`final`/`animation`), frame(s), sample/time budget; active-AOV list Open — Phase 09 |
| `STOP_RENDER` | add-on → bridge | request → ack | Decided: correlates to the `id` of the `START_RENDER` being cancelled |
| `FRAME_UPDATE` | bridge → add-on, unsolicited/streamed | correlates to owning `START_RENDER`'s `id` | Decided: never carries inline pixel data — carries a bulk-transport reference (shared-memory handle / socket-stream token per [FRAMEBUFFER_PROTOCOL.md](FRAMEBUFFER_PROTOCOL.md), still **Open — Phase 04**), plus sample-count/sequence number so stale frames can be dropped |
| `RENDER_COMPLETE` | bridge → add-on, terminal | correlates to owning `START_RENDER`'s `id` | Decided: terminal signal (converged, or cleanly stopped via `STOP_RENDER`) carrying final stats + a `cancelled` flag; distinct from progressive `FRAME_UPDATE` |
| `ERROR` | bridge → add-on (primary path) | correlates to the failing request's `id`, or absent for an async/unsolicited failure | Decided: `category` (1–5 per [ERROR_MODEL.md](ERROR_MODEL.md)), machine-readable `code`, human `message`, optional object/datablock reference |

`UPDATE_OBJECT`/`UPDATE_CAMERA`/`UPDATE_MATERIAL` are three message types rather than one
generic "update a thing" blob because they target structurally different RDL2 objects
(`Geometry`, `Camera`, `Material` built via `BsdfBuilder` — see SCENE_TRANSLATION.md) with
unrelated field sets and unrelated "does this require pausing the render" classification
(LIFECYCLE.md, Open — Phase 06/07). Splitting them lets each payload be validated against its
own schema instead of a single loosely-typed catch-all.

## Bulk data stays out of the envelope (decided)
Per DIRECT_BRIDGE_TARGET.md rule 4 and FRAMEBUFFER_PROTOCOL.md: mesh arrays and
framebuffer/AOV pixels are never inlined as JSON/dict arrays inside a control message. Where a
control message needs to refer to bulk data (`FRAME_UPDATE`, and eventually large mesh
payloads once Phase 06 measures whether `UPDATE_OBJECT` needs the same treatment), it carries
a *reference* (handle/token/offset/size) into the bulk transport, resolved separately from
message parsing. This keeps the schema in this document valid regardless of whether the bulk
transport ends up being shared memory, a binary socket stream, or something else — only the
reference format changes.

## Encoding independence (decided)
This document specifies the envelope and message set at the field/type level, not as a wire
format. Phase 04's first implementation may serialize this exactly as JSON (each message a
JSON object with `protocol_version`/`type`/`id`/`payload` keys, validated against a schema —
e.g. `dataclasses` + a validation step, or a JSON Schema document — never an unchecked
`json.loads()` result passed straight into scene construction). A later switch to
FlatBuffers/Cap'n Proto/shared-memory framing (PROTOCOL.md "exact wire format — Open") changes
only the serialization of the same envelope and message set defined here, not the contract
itself — this is the point of fixing the message-level contract before the transport
technology is chosen.

## Decided vs. open summary
| Aspect | Status |
|---|---|
| Four-field envelope (`protocol_version`, `type`, `id`, `payload`) | **Decided (this document)** |
| `protocol_version` is a single monotonic integer, bumped only on breaking change | **Decided (this document)** |
| Fixed message-type enum (11 types listed above) | **Decided (this document)** |
| `HELLO` always first, both directions; failure ends the connection before any scene exchange | **Decided (this document)** |
| `CAPABILITIES` separate from `HELLO`, additive, no version bump per flag | **Decided (this document)** |
| Unknown field inside a known message → ignored; unknown message `type` → hard `ERROR` | **Decided (this document)** |
| `UPDATE_OBJECT`/`UPDATE_CAMERA`/`UPDATE_MATERIAL` as distinct types | **Decided (this document)** |
| `FRAME_UPDATE`/bulk payloads carry a reference, never inline arrays | **Decided (this document)**; reference format **Decided — Phase 04**: a POSIX shared-memory segment name (string) plus width/height/channels/dtype/byte_size — see `docs/bridge/FRAMEBUFFER_PROTOCOL.md`. |
| Wire encoding | **Decided — Phase 04**: JSON (via JsonCpp) over a 4-byte little-endian length-prefixed frame. See `docs/evidence/phase04/`. |
| Exact per-message payload field layout (mesh, camera, light) | **Decided and implemented — Phase 06**, owned by [SCENE_TRANSLATION.md](SCENE_TRANSLATION.md); material payload layout remains **Open — Phase 07** |
| `CAPABILITIES` flag vocabulary | **Open**, grows per phase |
| `protocol_version` range/negotiation across independently-upgraded binaries | **Open**, not before Phase 11 |
