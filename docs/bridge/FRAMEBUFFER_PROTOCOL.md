# Framebuffer / AOV Protocol

Status: **TARGET DESIGN, not an implementation claim.** See [PROTOCOL.md](PROTOCOL.md) for
status conventions. Authoritative acceptance criteria live in
`docs/phases/04-direct-bridge-prototype.md` (minimal return path),
`docs/phases/08-interactive-viewport.md` (progressive delivery) and
`docs/phases/09-final-render-aovs-animation.md` (final AOVs/EXR).

## What this covers
Delivery of rendered pixel data — beauty and AOVs, progressive and final — from
`moonray_bridge` back to the Blender add-on, for both the Rendered Viewport and F12/EXR
output paths.

## Pipeline shape
```text
MoonRay RenderContext
        ↓  progressive render-buffer snapshot / AOV snapshot
moonray_bridge framebuffer message   (this contract)
        ↓  bulk binary / shared-memory transport (never per-pixel Python)
Blender add-on
        ↓
  viewport:  RenderEngine.bl_use_preview + tag_redraw progressive update
  final:     RenderResult passes → Compositor / EXR
```

## Decided (from `docs/project/ARCHITECTURE.md`)
- MoonRay exposes progressive render-buffer snapshots and AOV snapshots off `RenderContext`
  — the bridge reads these, it does not reimplement progressive accumulation.
- Bulk framebuffer/AOV payloads use an efficient binary or shared-memory strategy; no
  per-pixel/per-element Python transport.
- Snapshot cadence/strategy is a candidate for shared memory or a ring buffer "if benchmark
  justifies it" — not committed a priori.
- Viewport (Phase 08, progressive) and final render (Phase 09, complete + AOVs + EXR) are
  distinct delivery modes built on the same underlying snapshot mechanism; do not conflate
  their acceptance criteria.
- Render cancellation must be representable at this layer (Phase 09: "Failures/cancel do not
  corrupt later renders").

## Open — resolved by evidence in later phases
| Question | Target phase |
|---|---|
| ~~Exact transport~~ | **Decided — Phase 04**: POSIX shared memory (`shm_open`/`mmap`), one named segment per rendered frame, referenced by name in the control-plane reply — never a ring buffer or mapped file in this phase. `snapshotRenderBuffer()`'s output is already a contiguous array, so publishing is a single `memcpy`. Revisit ring-buffer/backpressure design in Phase 08/10 once progressive delivery exists. See `docs/evidence/phase04/`. |
| Snapshot cadence for the viewport (fixed interval, sample-count threshold, adaptive) | Phase 08 |
| ~~Pixel/channel layout on the wire~~ | **Decided — Phase 04**: interleaved RGBA float32 — the native layout of RDL2's `fb_util::RenderBuffer` (`PixelBuffer<Vec4f>`), copied as-is with no conversion. |
| AOV registration handshake (which AOVs are active, their names/types) | Phase 09 |
| Mapping of MoonRay AOV snapshots to Blender `RenderPass` names (`Combined`, `Depth`,
  `Normal`, `Cryptomatte`, ...) | Phase 09 |
| Multi-frame/animation buffer lifecycle (reuse vs. reallocate per frame) | Phase 09 |
| Backpressure/flow control if the add-on cannot consume snapshots fast enough | Phase 08/10 |

## Non-goals
- Distributed/network framebuffer aggregation (Arras-style) — out of scope for the direct
  bridge (`docs/phases/04-direct-bridge-prototype.md` out-of-scope: distributed networking).
- Guaranteeing "unbounded AOV feature parity" with other renderers
  (`docs/phases/09-final-render-aovs-animation.md` out-of-scope).

## Relationship to other contract documents
- Cancellation and mid-render bridge failure surface through [ERROR_MODEL.md](ERROR_MODEL.md).
- Render-mode transitions (idle → rendering → snapshotting → done/cancelled) are owned by
  [LIFECYCLE.md](LIFECYCLE.md); this document only covers the pixel-data payload itself.
