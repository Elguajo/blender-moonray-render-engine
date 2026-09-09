# Direct Bridge Target Design

This document is a **target**, not an implementation claim.

Detailed per-topic contract (message schema/versioning, scene translation, framebuffer/AOV
delivery, error model, lifecycle) lives under [`docs/bridge/`](../bridge/PROTOCOL.md); this
page stays the short product-level summary.

## Product surface
```text
Blender
└── Render Engine: MoonRay
    ├── Rendered Viewport
    ├── F12
    ├── Animation
    └── Render passes / Compositor
```

## Process boundary
```text
Blender add-on                     moonray_bridge
──────────────                     ──────────────
RenderEngine          IPC          RenderContext
Depsgraph        ───────────────▶   Scene/RDL2 state
Settings         ◀───────────────   Progress/errors
Viewport              bulk          framebuffer/AOVs
               ◀═════════════════   shared/binary data
```

## Design rules
1. No Hydra dependency in normal production startup.
2. Bridge protocol is versioned from first usable prototype.
3. Local-only transport by default.
4. Bulk arrays/images must not be serialized with Python element loops.
5. Blender should survive bridge termination and allow restart/retry.
6. Full-scene sync is acceptable for the first F12 milestone; incremental updates become mandatory before viewport production acceptance.
7. Do not pick a serialization technology until Phase 04 requirements are measured.
8. Do not optimize into an in-process plugin until Phase 10 evidence shows the process boundary is the bottleneck.
