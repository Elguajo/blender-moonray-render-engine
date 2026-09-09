# Error Model

Status: **TARGET DESIGN, not an implementation claim.** See [PROTOCOL.md](PROTOCOL.md) for
status conventions. Authoritative acceptance criteria live in
`docs/phases/04-direct-bridge-prototype.md` (malformed input / crash-restart),
`docs/phases/06-geometry-camera-lights.md` and
`docs/phases/07-materials-textures-instances.md` (unsupported-feature signaling).

## Error categories (decided shape, from `docs/project/ARCHITECTURE.md`)

### 1. Scene payload validation errors
Corrupt or unsupported bridge scene messages must fail validation **before** they mutate the
native MoonRay/RDL2 renderer state, where possible ("Corrupt/unsupported scene payload must
fail validation before native renderer mutation where possible" — ARCHITECTURE.md failure
isolation). This applies even though the add-on is normally the only client, because the
bridge protocol accepts local input defensively by design.

### 2. Unsupported-feature signaling
Object/light/material/node types outside the accepted support matrix must fail or fall back
**explicitly** — never silently mis-render:
- `docs/phases/06-geometry-camera-lights.md`: "Unsupported types fail or fall back
  explicitly, never silently mis-render."
- `docs/phases/07-materials-textures-instances.md`: "Unsupported nodes are surfaced
  explicitly."

This is a distinct category from validation errors: the payload is well-formed, but the
*feature* it describes is outside current scope. The bridge/add-on must be able to tell the
user which object/material/node was skipped and why, not just that "something" was
unsupported.

### 3. Native MoonRay render errors
Errors raised during RDL2 scene construction or MoonRay rendering itself (e.g. RDL2
`except::KeyError` for a missing scene object/class, per
`docs/vendor/openmoonray/developer-reference/scene_rdl2-library.md`). These occur after
validation has already accepted the payload, so they represent either an internal bridge
translation bug or a genuine native-runtime failure, not a client-input problem.

### 4. Bridge process crash
- Must be detected by the Blender integration (not assumed away).
- Blender must retain the open `.blend` session and surface restart/retry diagnostics —
  a bridge crash must never take the DCC down with it (ARCHITECTURE.md failure isolation;
  this is the core reason the bridge is a separate process — ADR-0002).
- Recovery/watchdog *policy* (auto-restart vs. manual retry, state resync after restart) is
  Phase 11 scope (`docs/phases/11-stability-packaging.md`: "Bridge watchdog/restart policy").
- Phase 04 acceptance already requires: "Bridge process crash/restart does not corrupt
  client process."

### 5. Version/handshake mismatch
Add-on and bridge must be able to detect an incompatible protocol/build version before
attempting to exchange scene or framebuffer data. The `HELLO` handshake and its
`VERSION_MISMATCH` rejection shape are decided in [MESSAGE_SCHEMA.md](MESSAGE_SCHEMA.md); the
exact wire encoding of that handshake is Phase 04 scope (see also [LIFECYCLE.md](LIFECYCLE.md)).

## Logging
Native bridge logs/evidence must be persisted outside Blender's stdout capture alone
(ARCHITECTURE.md security/trust boundaries) — Blender's console is not an acceptable sole
error-reporting channel for the bridge. Exact log location/format/rotation is Phase 11 scope
("Document troubleshooting and log collection").

## Open — resolved by evidence in later phases
| Question | Target phase |
|---|---|
| Exact `ERROR.code` taxonomy (machine-readable codes per category; `ERROR` message shape decided in [MESSAGE_SCHEMA.md](MESSAGE_SCHEMA.md)) | Phase 04 |
| How validation errors are attributed to a specific Blender object/datablock in the UI | Phase 06/07 |
| Auto-restart vs. manual-retry default policy | Phase 11 |
| Structured log format/location/rotation | Phase 11 |
| Partial-render recovery (resume vs. restart) after mid-render crash | Phase 11 |

## Explicitly out of scope
- Treating "renderer produced a plausible-looking image" as success without evidence — this
  document governs *signaling*, not what counts as a passing render (see phase acceptance
  criteria and `AGENT_HANDOFF.md`: "Never claim build/render/test/performance success unless
  observed").
