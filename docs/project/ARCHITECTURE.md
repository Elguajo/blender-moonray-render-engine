# Architecture — Direct MoonRay Render Engine for Blender 5.2+

Status: SELECTED / DIRECT BRIDGE PRIMARY

Decisions:
- `docs/decisions/ADR-0001-wsl2-linux-host-boundary.md`
- `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md`

## Recommended stack
- Workstation host: Windows 11.
- Linux execution boundary: WSL2 + WSLg.
- Linux baseline: Rocky Linux 9.x, exact release persisted by Phase 02 evidence.
- DCC baseline: Blender 5.2.1 LTS Linux.
- Blender integration: Python add-on + `bpy.types.RenderEngine` lifecycle/UI/pass integration.
- Native runtime: separate `moonray_bridge` process written in C++ unless Phase 04 evidence strongly supports a different minimal native boundary.
- Renderer API: MoonRay `RenderContext` + scene_rdl2/RDL2 APIs.
- Control transport: local IPC; exact protocol selected in Phase 04 from measured requirements.
- Bulk transport: shared memory and/or efficient binary transport for geometry/framebuffer/AOV payloads; no Python per-element production transport.
- Compute: CPU baseline first; XPU/CUDA separate gate.
- Hydra/hdMoonray: non-primary reference/fallback/benchmark path under `experiments/hydra/`.

## Why this fits
The product goal is not merely to launch MoonRay externally; it is to make MoonRay behave like a Blender render engine. Blender's RenderEngine API owns DCC lifecycle, F12, viewport and pass integration, while MoonRay exposes native rendering/scene facilities suitable for an application bridge.

A separate native process is the initial production boundary because Blender and MoonRay each bring large native dependency graphs. Keeping them in distinct processes avoids making Blender stability depend on C++ ABI/symbol compatibility across MoonRay/TBB/OIIO/OpenEXR/etc. It also enables bridge restart/recovery without necessarily terminating the DCC.

Hydra remains useful for comparison and as an emergency fallback, but it is no longer a mandatory dependency or architecture constraint.

## System shape
```text
Windows 11 workstation
│
└─ WSL2 + WSLg / Rocky Linux 9.x
   │
   ├─ Blender 5.2.1 LTS
   │  │
   │  └─ MoonRay Blender add-on
   │     ├─ bpy.types.RenderEngine
   │     ├─ depsgraph observer
   │     ├─ scene translator
   │     ├─ render settings / UI
   │     ├─ viewport presentation
   │     └─ RenderResult / pass integration
   │              │
   │              ├─ Control IPC ───────────────┐
   │              └─ Bulk binary/shared memory ┤
   │                                             ▼
   └──────────────────────────────────── moonray_bridge
                                                 │
                                                 ├─ Scene state / RDL2
                                                 ├─ incremental updates
                                                 ├─ MoonRay RenderContext
                                                 ├─ progressive snapshots
                                                 └─ AOV snapshots
```

## Runtime responsibilities

### Blender add-on
- register/select MoonRay Render Engine;
- expose render settings and supported feature UI;
- inspect depsgraph changes;
- serialize canonical scene updates without doing heavy native conversion in slow Python loops;
- start/stop/recover Bridge Process;
- display progressive viewport frames;
- populate final RenderResult and registered passes;
- surface actionable errors/log references.

### Native Bridge Process
- own MoonRay/scene_rdl2 native dependencies;
- own render context lifetime and renderer threads;
- convert accepted bridge schema to RDL2/MoonRay objects;
- apply incremental scene changes only when MoonRay lifecycle permits;
- snapshot beauty/AOV buffers;
- publish progress/status/errors;
- isolate crashes and support restart protocol.

## Data-plane principle
Use Python for orchestration and Blender API access; use compact/native binary paths for bulk data.

Candidate split (to be proven, not blindly fixed):
- control/status/settings → local socket/IPC messages;
- mesh arrays / transforms / texture metadata → packed binary messages or shared memory;
- progressive beauty/AOV frames → shared memory/ring buffer if benchmark justifies it.

The exact wire/schema format is a Phase 04 decision. Do not prematurely commit to protobuf/Cap'n Proto/FlatBuffers/etc. without requirements/evidence.

## Scene lifecycle
```text
Blender depsgraph change
        ↓
change classification
        ↓
canonical bridge update
        ↓
Bridge validates + maps to RDL2
        ↓
MoonRay update while not rendering (where required)
        ↓
restart/continue render according to renderer lifecycle
        ↓
progressive framebuffer/AOV snapshot
        ↓
Blender viewport / RenderResult
```

## Failure isolation
- Bridge crash must be detected by Blender integration.
- Blender should retain the `.blend` session and surface restart/retry diagnostics.
- Corrupt/unsupported scene payload must fail validation before native renderer mutation where possible.
- Native logs/evidence should be persisted outside Blender stdout alone.

## Sources of truth
- Outcome/scope → `docs/project/PROJECT_BRIEF.md`
- WSL2 host boundary → ADR-0001
- Direct Bridge decision → ADR-0002
- Current phase/order → `docs/project/ROADMAP.md`
- Resume point → `docs/project/NEXT_SESSION.md`
- Feasibility evidence → `docs/research/03-direct-bridge-feasibility.md`

## Security/trust boundaries
- bridge protocol accepts local untrusted/corrupt input defensively even if normally produced by the add-on;
- do not expose bridge network listeners beyond localhost/Unix socket by default;
- downloaded upstream artifacts must be pinned/checksummed or reproducibly built;
- large asset paths and output paths must not permit accidental traversal outside operator-selected locations;
- do not execute scene-provided shell commands or arbitrary scripts through bridge messages.

## Operational assumptions
- source/build/install/cache trees live on Linux-native WSL filesystem unless measured evidence proves otherwise;
- production project/assets remain separable from build/runtime artifacts;
- Bridge Process is launched and version-checked by the Blender integration/launcher;
- Blender/MoonRay upgrades are compatibility migrations requiring verification;
- CPU behavior is acceptance baseline; XPU is additive.

## Architecture-change triggers
- out-of-process transport is proven to be the dominant unavoidable performance bottleneck after optimized shared-memory/binary implementation;
- MoonRay public/internal APIs required by the bridge are too unstable for maintainable integration;
- WSL2 cannot meet GUI/runtime/performance/stability needs on target workstation;
- a future official MoonRay Blender integration becomes maintained and meets the project's production requirements;
- in-process integration becomes justified by measured benefit and a controlled ABI strategy.
