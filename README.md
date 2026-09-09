# Direct MoonRay Render Engine for Blender 5.2+

![Status](https://img.shields.io/badge/status-experimental-orange)
![Blender](https://img.shields.io/badge/Blender-5.2.1%20LTS-blue)
![Platform](https://img.shields.io/badge/platform-WSL2%20%2F%20Linux-lightgrey)
![Integration](https://img.shields.io/badge/integration-direct%20bridge-purple)
![License](https://img.shields.io/badge/license-GPL--3.0--or--later-green)

A community, production-oriented effort to make **OpenMoonRay** available as a real **Blender 5.2+ Render Engine** through a **direct MoonRay bridge** — without making Hydra/hdMoonray a required runtime dependency.

> [!IMPORTANT]
> This project is experimental and is **not affiliated with or endorsed by DreamWorks Animation, the Academy Software Foundation, the Blender Foundation, or their contributors**. MoonRay, Blender, OpenUSD and related names belong to their respective owners.

## Why direct bridge?

The target is the Blender workflow users expect:

```text
Render Properties → Render Engine → MoonRay
Rendered Viewport → MoonRay progressive render
F12 → MoonRay → Blender Render Result
Compositor → MoonRay beauty/AOV passes
```

The primary architecture deliberately removes Hydra from the required render path:

```text
Windows 11 workstation
└── WSL2 + WSLg
    └── Rocky Linux 9.x
        ├── Blender 5.2.1 LTS
        │   └── Blender add-on / bpy.types.RenderEngine
        │       ├── depsgraph + scene translator
        │       ├── Rendered Viewport client
        │       └── F12 / RenderResult / passes
        │
        └── moonray_bridge (separate native process)
            ├── IPC control channel
            ├── shared/binary scene data transport
            ├── scene_rdl2 / RDL2 scene state
            └── MoonRay RenderContext
                ├── CPU baseline
                └── XPU only after separate validation
```

Hydra/hdMoonray is retained under [`experiments/hydra/`](experiments/hydra/) only as a **reference, fallback and benchmark path**.

## Project status

Development is evidence-gated. A phase is complete only after its acceptance criteria have been observed and persisted.

| Phase | Status | Goal |
|---|---:|---|
| 00 | ✅ | Scope and durable baseline |
| 01 | ✅ | Compatibility research and WSL2 host decision |
| 02 | 🚧 | WSL2 / Rocky Linux / Blender host foundation |
| 03 | ⏳ | Reproducible native MoonRay runtime |
| 04 | ⏳ | Direct MoonRay bridge prototype |
| 05 | ⏳ | Blender `RenderEngine` integration |
| 06 | ⏳ | Geometry, camera and lights translation |
| 07 | ⏳ | Materials, textures and instances |
| 08 | ⏳ | Interactive Rendered Viewport |
| 09 | ⏳ | F12, AOVs, animation and EXR |
| 10 | ⏳ | Incremental updates and performance |
| 11 | ⏳ | Stability, packaging and installer |
| 12 | ⏳ | Production acceptance and release |

Canonical state: [`docs/project/ROADMAP.md`](docs/project/ROADMAP.md).

## Architectural principles

- **MoonRay remains the renderer.** This project implements DCC integration, not a new path tracer.
- **Direct bridge is primary.** Hydra is not a mandatory runtime layer.
- **Crash isolation first.** MoonRay initially runs out-of-process so dependency/ABI faults do not take Blender down with it.
- **Python orchestrates; native code moves bulk data.** Python should not loop over millions of vertices/pixels for production transport.
- **Incremental updates are mandatory for interactive use.** Camera/object/material changes should not force full scene export when avoidable.
- **CPU first.** GPU/XPU support is a separate evidence gate.
- **No performance claims without benchmarks.** Hydra is not called "slow" by assumption; direct vs Hydra performance must be measured later.

## Goals

- selectable `MoonRay` engine in Blender;
- progressive Rendered Viewport;
- F12/final frame and animation rendering;
- Blender camera, geometry, lights and a useful material subset translated to MoonRay/RDL2;
- Beauty plus required AOV/pass integration with Blender RenderResult/Compositor;
- incremental scene updates suitable for lookdev;
- reproducible WSL2/Linux setup and pinned upstream runtime;
- explicit PASS/PARTIAL/FAIL compatibility and known-limitations matrix.

## Non-goals for the first production release

- native Windows port of MoonRay;
- rewriting MoonRay;
- full parity with every Cycles/Eevee shader node;
- distributed Arras render farm before single-workstation acceptance;
- forcing an in-process MoonRay library into Blender before crash-isolated bridge behavior is validated;
- claiming XPU support from CUDA visibility alone.

## Quick start

Current work is **Phase 02**. Read in this order:

1. [`docs/project/PROJECT_BRIEF.md`](docs/project/PROJECT_BRIEF.md)
2. [`docs/project/ARCHITECTURE.md`](docs/project/ARCHITECTURE.md)
3. [`docs/project/ROADMAP.md`](docs/project/ROADMAP.md)
4. [`docs/project/NEXT_SESSION.md`](docs/project/NEXT_SESSION.md)
5. [`docs/phases/02-host-runtime-foundation.md`](docs/phases/02-host-runtime-foundation.md)
6. [`docs/runbooks/PHASE02_HOST_SETUP.md`](docs/runbooks/PHASE02_HOST_SETUP.md)

Do not start MoonRay/bridge implementation before Phase 02 has real-workstation evidence.

## Repository map

| Area | Location |
|---|---|
| Blender integration code | [`addon/`](addon/) |
| Native MoonRay bridge | [`bridge/`](bridge/) |
| Hydra comparison/fallback | [`experiments/hydra/`](experiments/hydra/) |
| Product scope | [`docs/project/PROJECT_BRIEF.md`](docs/project/PROJECT_BRIEF.md) |
| Architecture | [`docs/project/ARCHITECTURE.md`](docs/project/ARCHITECTURE.md) |
| Roadmap | [`docs/project/ROADMAP.md`](docs/project/ROADMAP.md) |
| Current resume state | [`docs/project/NEXT_SESSION.md`](docs/project/NEXT_SESSION.md) |
| Phase specifications | [`docs/phases/`](docs/phases/) |
| Completion evidence | [`docs/completions/`](docs/completions/) |
| ADRs | [`docs/decisions/`](docs/decisions/) |
| Research | [`docs/research/`](docs/research/) |
| Design notes | [`docs/design/`](docs/design/) |
| Runbooks | [`docs/runbooks/`](docs/runbooks/) |

## Contributing

Contributions are welcome around Blender integration, MoonRay/RDL2 scene translation, IPC/shared-memory transport, materials, AOVs, viewport display, performance and reproducibility.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a PR. Compatibility/performance claims require reproducible evidence; "it should be faster" is not evidence.

## Issue types

- **Bug** — reproducible failure.
- **Compatibility report** — exact Blender/Bridge/MoonRay/platform combination.
- **Performance report** — benchmark with scene/build/settings/evidence.
- **Feature request** — proposed capability.
- **Documentation** — incorrect or missing docs.

Security issues should not be public; see [`SECURITY.md`](SECURITY.md).

## License

Project-owned source code is licensed under **GPL-3.0-or-later**. See [`LICENSE`](LICENSE). Upstream projects keep their respective licenses; this repository does not relicense Blender, MoonRay, OpenUSD, hdMoonray or other third-party software.
