# Next Session — Direct MoonRay Render Engine for Blender 5.2+

## Current state
Phases 00–06 are complete. No phase is currently `[>]`. **Phase 07
(Materials, textures and instances, `docs/phases/07-materials-textures-instances.md`)
requires explicit user approval before it may begin.**

The verified foundation physically exists on the workstation `DESKTOP-9O2U790`:

```text
Windows 11 build 10.0.26100.9445
└── WSL 2.6.3.0 + WSLg 1.0.71, kernel 6.6.87.2
    └── Rocky Linux 9.8 — distro "MoonRay-Rocky9"
        ├── Blender 5.2.1 LTS Linux, GUI verified through WSLg (Phase 02/05)
        ├── MoonRay CPU runtime, built from pinned source, render-verified
        ├── moonray_bridge (bridge06 build): structured protocol_version=2,
        │   native RDL2 SceneObject construction (Phase 06)
        └── addon/ MoonRay Blender add-on: multi-object mesh/camera/light
            translation, F12/background render-verified
```

## Phase 06 outcome (2026-09-11) — read before touching `bridge/` or `addon/scene_translator.py`
The bridge protocol was extended from Phase 04/05's raw `.rdla`-path
`CREATE_SCENE` to a structured schema (`docs/decisions/ADR-0005-structured-scene-protocol.md`):
`CREATE_SCENE` now takes `{scene_variables: {image_width, image_height,
pixel_samples}}` and builds an empty scaffold (`SceneVariables` +
`GeometrySet` + `Layer` + `LightSet` + one placeholder `DwaBaseMaterial`)
directly in a fresh `RenderContext`'s `SceneContext`; `UPDATE_OBJECT`
(`op` ∈ `create`/`update`/`delete`, `kind` ∈ `mesh`/`light`) and
`UPDATE_CAMERA` populate it via real RDL2 `SceneObject::set<T>()` calls in
`bridge/src/SceneBuilder.cpp`. `protocol_version` bumped 1 → 2 (breaking
payload-shape change). `addon/scene_translator.py` (replacing and deleting
`addon/scene_writer.py`) translates any number of Blender mesh objects,
native-maps Blender's own light types (`POINT`/`SUN`/`SPOT`/`AREA` →
`Sphere`/`Distant`/`Spot`/`Rect`/`DiskLight`, `ELLIPSE` shape fails
explicitly), and maps the confirmed camera unit table. Full detail:
`docs/completions/06-geometry-camera-lights.md`, `docs/evidence/phase06/`.

### The GeometrySet invariant — load-bearing, confirmed by source (Phase 06 pre-flight)
A `Geometry` must be a member of a `GeometrySet` in the `SceneContext` to
ever reach the BVH/render — being assigned in the `Layer` is **not**
sufficient on its own. Confirmed by reading
`moonray/lib/rendering/rt/GeometryManager.cc::collectPrimitives()` at the
pin in `UPSTREAM_LOCK.json`: it walks `GeometrySet` membership exclusively;
`Layer` assignment is a filter applied *inside* that walk. A geometry in the
`Layer` but no `GeometrySet` silently never renders — no error, no warning.
Every geometry-creating code path (`SceneBuilder.cpp::applyMeshUpdate`) adds
to both. Full citation: `docs/bridge/SCENE_TRANSLATION.md` "Mesh geometry".

### A real, root-caused, and now-fixed light bug — load-bearing, read before adding any new light-dependent code
Phase 05 found (but did not root-cause) that `SphereLight`/`DistantLight`
failed to illuminate this project's own geometry and shipped an un-root-
caused axis-snap workaround. Phase 06 root-caused the `DistantLight` (and,
by the same confirmed source mechanism, `SpotLight`/`RectLight`/`DiskLight`)
part of it: every one of those classes' `update()`
(`moonray/lib/rendering/pbr/light/*.cc`, pinned commit) composes
`node_xform` with a built-in 180-degree rotation about local X ("for
consistency with DiskLight," per that source's own comment) before deriving
the light's actual illumination direction/frame. The naive "local Z axis =
intended direction" construction Phase 05 used therefore illuminated the
mirror image (about local X) of the intended direction — confirmed against
source *and* empirically (two independent hand-built scenes through the
unmodified Phase 04 bridge, axis-aligned and tilted, both went from flat
black to correctly lit once corrected). **This is a bug in this project's
own code, not MoonRay** — no upstream report needed.
`addon/scene_translator.py::light_xform_to_rdl2_mat4()` is the fix; the
axis-snap workaround is gone. **Only `DistantLight` was independently
re-rendered end-to-end** (both cases); `SpotLight`/`RectLight`/`DiskLight`
share the identical source-verified fix by construction but were not
independently re-rendered — re-verify end-to-end before trusting one of
them in a later phase if anything looks visually wrong.
`SphereLight`'s *original* Phase 05 failure (with real Blender-derived
data) was **not** reproduced by a fresh, straightforward control case in
Phase 06 and remains genuinely unexplained if it resurfaces — see
`docs/evidence/phase06/light-orientation-fix/README.md` "What remains open"
before assuming this fix also covers it.

### A known, open limitation: mid-session delete-after-render
`UPDATE_OBJECT(op=delete)` reliably removes an object if issued **before**
the first `START_RENDER` of a bridge session. Deleting an object **after** a
render has already happened in the same live session was tried and observed
to **not** reliably remove the geometry from a subsequent render —
`RenderContext::startFrame()`'s `mSceneUpdated` path uses
`rt::ChangeFlag::UPDATE` (not `ALL`), and `GeometryManager`'s `UPDATE` path
appears additive/refresh-oriented, not proven to shrink an already-built
BVH when a `GeometrySet` member is removed. This does not block Phase 06
(the add-on launches one fresh bridge process per render,
`addon/bridge_launcher.py`, and always sends `create` — it never hits this
case) but **Phase 08's incremental viewport must solve this before relying
on mid-session delete** — likely by forcing `ChangeFlag::ALL` on a delete,
or another `RenderContext` mechanism not yet identified. Full detail:
`docs/bridge/SCENE_TRANSLATION.md` "Update / delete semantics",
`docs/decisions/ADR-0005-structured-scene-protocol.md` "Costs".

### Bugs found and fixed in Phase 06 (beyond the light orientation fix)
1. **`Mesh.calc_normals_split()` no longer exists in Blender 5.2** (removed
   upstream; split normals are computed on demand now). Caught only by a
   real Blender render, not by the bridge-level smoke tests. If you add mesh
   attribute extraction elsewhere, do not call this method.
2. **Wrong RDL2 attribute name for camera-ray visibility**: `visible_camera`
   used instead of the real `visible_in_camera` (confirmed via
   `rdl2_print -c RdlMeshGeometry`), in both `SceneBuilder.cpp` and
   `scene_translator.py`. If you add more per-object attribute names by
   hand, ground them against `rdl2_print` output, not memory/assumption —
   this is exactly the mistake `rdl2_print` exists to catch and it still
   slipped through once.

### Bridge protocol was changed — `protocol_version` is now 2
Any external client (including `bridge/client/bridge_client.py`, the
Phase-04-era test-only client, already updated) must send
`protocol_version: 2` and use the new `CREATE_SCENE`/`UPDATE_OBJECT`/
`UPDATE_CAMERA` payload shapes — see `docs/bridge/MESSAGE_SCHEMA.md` and
`docs/bridge/SCENE_TRANSLATION.md`. `UPDATE_MATERIAL`'s payload is still
`NOT_IMPLEMENTED` (category 2 `ERROR`) — Phase 07 scope.

## Durable decisions
- Windows 11 workstation host; Blender + MoonRay-facing runtime execute under WSL2/WSLg Linux.
- Blender baseline: 5.2.1 LTS until an explicit compatibility migration.
- Direct Blender `RenderEngine` ↔ MoonRay bridge is primary (ADR-0002).
- MoonRay runs in a separate native Bridge Process for crash/dependency isolation
  (ADR-0002, corroborated by ADR-0003's survey of V-Ray/Octane for Blender).
- Bridge IPC: Unix domain socket, JSON envelope (JsonCpp) with 4-byte
  length-prefixed framing; bulk framebuffer data via POSIX shared memory,
  interleaved RGBA float32 (ADR-0004).
- Bridge scene protocol: structured `CREATE_SCENE`/`UPDATE_OBJECT`/`UPDATE_CAMERA`,
  native RDL2 `SceneObject` construction in the bridge, not `.rdla`-file
  round-tripping (ADR-0005, Phase 06). `protocol_version` is 2.
- Hydra/hdMoonray is reference/fallback/benchmark only; never silently restore it as primary.
- CPU is the mandatory first render baseline. XPU/CUDA is a separate evidence gate.
- Do not claim Direct Bridge is faster than Hydra until Phase 10 benchmark evidence exists.
- No non-local network listener by default (satisfied structurally: the bridge has no
  `AF_INET` code path at all, not just a disabled-by-default flag).
- The bridge process lifecycle is one-shot per render (launch, use, tear down), not a
  persistent long-lived process across renders — revisit only with a real measured need
  (e.g. Phase 08 viewport-latency, which will also need to solve the mid-session
  delete-after-render limitation above at the same time).
- Blender light types map natively onto RDL2 light classes (`POINT`→Sphere, `SUN`→Distant,
  `SPOT`→Spot, `AREA`→Rect/Disk by shape); Blender's light UI/type enum is never replaced by
  a MoonRay-native one (Phase 06 decision B — keeps scenes portable to Cycles/EEVEE).
- Every mesh currently shares one placeholder `DwaBaseMaterial` (`kDefaultMaterialName` in
  `SceneBuilder.cpp`) — real per-object material translation is Phase 07's job.

## Key facts carried forward from Phase 03
- Installed runtime: `/root/moonray-blender/install/openmoonray` — `bin/` (incl. `moonray`,
  `rdl2_json_exporter`, `denoise`, `rdl2_print`, `rdl2_convert`), `lib64/`, `include/`,
  `rdl2dso/` (348 DSOs), `coredata/`.
- Third-party dependency build: `/opt/MoonRay/installs` (Linux-native ext4, upstream's own
  hardcoded default).
- Pinned source: `/root/moonray-blender/src/openmoonray` at superproject
  `b9b0ac29135b26e20a51edf9028558bb64df6700`; only `cmake_modules`, `scene_rdl2`,
  `mcrt_denoise`, `moonray`, `moonshine` are initialized. Hydra/Arras/USD/rats/moonray_gui
  submodules are deliberately uninitialized. Do not initialize them.
- Built CPU-only: `MOONRAY_USE_OPTIX=NO` in all four `CMakeCache.txt`. GPU/XPU is **not**
  proven on this machine and must not be claimed.
- Known-good test scene: `/root/moonray-blender/src/openmoonray/testdata/rectangle.rdla`
  (512×512, `DwaBaseMaterial`, `EnvLight`) — used by Phase 03/04's own tests and as a
  reference/control scene in Phase 05/06's light investigations.
- `rdl2_print` (installed runtime `bin/rdl2_print`) dumps SceneClass attributes/defaults/
  comments for any DSO on `RDL2_DSO_PATH` — use it to ground any new RDL2 object's exact
  attribute names before authoring code by hand, as Phase 05/06 did for
  `BoxGeometry`/`RdlMeshGeometry`/`DistantLight`/`SphereLight`/`SpotLight`/`RectLight`/
  `DiskLight`/`PerspectiveCamera`/`DwaBaseMaterial`/`SceneVariables`/`GeometrySet`/`Layer`/
  `LightSet` — and still ground new names this way even when confident (Phase 06 shipped a
  wrong attribute name once, `visible_camera` vs. the real `visible_in_camera`, despite
  having used `rdl2_print` for the rest of the attribute set).

## Verified host facts (Phase 02/03, observed)
- Distro: `MoonRay-Rocky9`, Rocky Linux 9.8, WSL2, root user, systemd active.
- Distro VHDX: `D:\01_DEV\moonray-blender-wsl\MoonRay-Rocky9`.
- Linux-native runtime root: `/root/moonray-blender` on ext4 `/dev/sdd` (~945 GB free).
- Blender: 5.2.1 LTS, hash `9e2066aef7ef`, at `/root/moonray-blender/tools/blender-current/blender`;
  launcher `~/bin/blender-moonray-host` (forces X11). Bundled Python 3.13.13.
- Hardware: Xeon E5-2690 v4 (28 threads), 31.8 GiB host RAM (15 GiB visible to WSL), RTX 3060 12 GB.
- Toolchain: gcc/g++ 11.5.0, cmake 3.31.8, ninja 1.10.2, system python3 3.9.25, git 2.52.0.
  `gdb` 16.3 (Phase 04) and `xdotool`/`libxdo`/`libXtst` (Phase 05, for GUI-evidence
  automation) are installed in the distro and remain available.
- **Known limitation:** WSLg OpenGL is software (`llvmpipe`) — Rocky's Mesa has no `d3d12`
  Gallium driver. Non-blocking for CPU rendering; a real input to Phase 08.

## Practical notes
- Enter the distro with `wsl -d MoonRay-Rocky9`; the repo is visible at
  `/mnt/d/01_DEV/blender-moonray-render-engine`.
- Keep all build trees under `/root/moonray-blender`, never on `/mnt/*`. Phase 06's bridge
  build lives at `/root/moonray-blender/build/bridge06` (separate from Phase 04's `bridge04`,
  which remains as untouched evidence).
- From Git Bash, prefix `wsl.exe` calls with `MSYS_NO_PATHCONV=1`.
- **Prefer piping scripts via stdin, or writing a file under the repo's `/mnt/d` tree and
  running it by path, over inline `bash -lc '...'` arguments** — short variables can get
  mangled through the interop, and longer/subprocess-spawning or variable-heavy inline
  commands were flaky for unclear reasons across Phase 04/05/06.
- Calling `wsl.exe` from PowerShell 5.1 needs `$env:WSL_UTF8=1` and tolerance for native
  stderr; see `Invoke-Wsl` in `scripts/windows/phase02_setup_wsl_rocky.ps1`.
- Do not overwrite `/root/moonray-blender/logs/phase03-rectangle.exr` or
  `logs/phase03-build/*.log` — Phase 03 evidence with recorded checksums.
- WSL sees 15 GiB RAM; `-j 8` was sufficient for every build so far.
- A crash class exists (Phase 04) that, at least once, appeared to destabilize the WSL2 VM
  itself (kernel fault register dump + a subsequent fresh boot sequence in `dmesg`), not just
  the one process. If a future session hits a similarly reproducible crash with implausibly
  large allocation requests, suspect a native lifetime bug before assuming it's environmental.
- The Blender GUI window, launched via WSLg, appears as a real Windows window (WSLg's own
  RDP-based integration) — a Windows-side screenshot tool can capture it directly. Mouse/
  keyboard automation from the Windows side was unreliable against this window; `xdotool`
  from inside the distro (`DISPLAY=:0`) was reliable for the Phase 05 GUI evidence. Phase 06's
  own evidence used `--background` mode instead (equivalent `RenderEngine.render()` code
  path, per Phase 05's own established precedent) and did not repeat the GUI F12 screenshot.
- `gh api -H "Accept: application/vnd.github.raw" repos/<owner>/<repo>/contents/<path>?ref=<sha>`
  is a reliable way to read pinned upstream source files directly (moonray/scene_rdl2 are not
  vendored locally, only their commit SHAs are pinned in `UPSTREAM_LOCK.json`) without cloning
  the whole repo — used throughout Phase 06's pre-flight and light-orientation root-cause work.

## Supporting repository infrastructure
- `UPSTREAM_LOCK.json` — canonical pinned upstream commits; do not choose new commits ad hoc.
- `configs/moonray-source-lock.json` — machine-readable CPU-baseline build manifest.
- `docs/research/03-upstream-pin-audit.md` — pin reconciliation and submodule classification.
- `docs/research/04-prior-blender-moonray-implementations.md` — survey of prior public
  MoonRay-for-Blender attempts.
- `docs/research/05-prior-art-harvest.md` — applied harvest (pitfall list, camera/mesh/light
  contracts) feeding directly into Phase 06/07; still worth reading for Phase 07's material
  mapping section (§7 "Phase 07").
- `docs/runbooks/PHASE03_MOONRAY_BUILD_PLAN.md` — original Phase 03 plan plus a correction note.
- `scripts/linux/phase03_*.sh`, `phase04_build_bridge.sh`, `phase06_build_bridge.sh` — the
  executed, reproducible build scripts for each phase so far. Phase 05 added no new build
  script (pure consumer of the Phase 04 binary); Phase 06 added `phase06_build_bridge.sh`
  (separate `bridge06` build directory, same configure/build shape).
- `docs/vendor/openmoonray/developer-reference/` — pinned local mirror of upstream docs.
  Search it for API topics rather than loading the tree into context. Ground exact attribute
  names via `rdl2_print` (installed runtime), not this doc alone — see "Key facts" above.
- `docs/bridge/*.md` — the bridge protocol contract. `SCENE_TRANSLATION.md`/`MESSAGE_SCHEMA.md`/
  `PROTOCOL.md` were substantially updated by Phase 06 (structured schema now Decided and
  implemented). `UPDATE_MATERIAL` payload, materials/instancing remain Open — Phase 07.
- `addon/` — the Blender add-on package. `scene_translator.py` (Phase 06) is the current
  translator; `scene_writer.py` (Phase 05) was deleted, superseded. `bridge_client.py` here
  is the add-on's own production copy, separate from `bridge/client/bridge_client.py`
  (test-only) — both updated to `protocol_version` 2 in Phase 06.
- `docs/evidence/phase06/` — Blender background-mode multi-object render, and
  `light-orientation-fix/` (the root-cause investigation trail: 5 hand-built `.rdla` control
  scenes plus their runners, read this before assuming a light-illumination bug is a new
  engine anomaly rather than a repeat of this one).

## Read first
1. `AGENTS.md` / `CLAUDE.md`
2. `docs/project/PROJECT_BRIEF.md`
3. `docs/project/ARCHITECTURE.md`
4. `docs/project/ROADMAP.md`
5. `docs/project/NEXT_SESSION.md` (this file)
6. `docs/completions/06-geometry-camera-lights.md` + `docs/evidence/phase06/` for what Phase 06
   actually proved, especially the light-orientation fix and the delete-after-render limitation
7. `docs/decisions/ADR-0002-direct-moonray-bridge-primary.md`,
   `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md`, and
   `docs/decisions/ADR-0005-structured-scene-protocol.md`
8. `docs/phases/07-materials-textures-instances.md` before Phase 07 is approved to start

## Mandatory phase protocol
1. Execute only the current approved phase.
2. Verify acceptance criteria with observed evidence.
3. Update the phase Completion Record.
4. Write/update `docs/completions/NN-<slug>.md` and `docs/evidence/phaseNN/`.
5. Update Architecture/ADR only for material decisions.
6. Mark the current phase `[x]` in Roadmap and activate the next phase only per the user's instruction.
7. Overwrite NEXT_SESSION with exact resume state.
8. Stop and ask in Russian: `Phase NN завершён. Переходим к Phase NN+1?`
9. Only after explicit approval execute the next phase.

## Planned sequence after Phase 06
- 07: materials/textures/instances (`DwaBaseMaterial` vs. `UsdPreviewSurface` choice is
  explicitly Open — see `docs/bridge/SCENE_TRANSLATION.md` "Materials"; `UPDATE_MATERIAL`
  wire payload; instancing via `RdlInstancerGeometry`).
- 08: progressive Rendered Viewport (watch the software-GL limitation; must also solve the
  mid-session delete-after-render limitation Phase 06 documented before incremental viewport
  updates can be trusted).
- 09: final/AOV/animation/EXR.
- 10: incremental updates + direct-vs-Hydra benchmark if Hydra comparison is available.
- 11: recovery/packaging/installer.
- 12: production acceptance/release.

## Reporting
Report observed facts only: Result, Manual check, Files changed, Validation, Important
decisions, Remaining risks. Never claim a renderer/build/test works unless actually observed.
