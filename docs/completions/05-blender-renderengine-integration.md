# Phase 05 Completion — Blender RenderEngine Integration and First F12 Frame

Status: COMPLETED
Completed: 2026-09-10
Workstation: `DESKTOP-9O2U790`, distro `MoonRay-Rocky9` (WSL2, Rocky Linux 9.8)

## Outcome
A Blender 5.2+ add-on (`addon/`) registers `MoonRay` as a selectable Render
Engine, launches and version-checks the Phase 04 `moonray_bridge` process,
translates Blender's default baseline scene (one camera + one mesh primitive
+ one light) into the `.rdla` format the bridge's existing `CREATE_SCENE`
already accepts, drives a synchronous `START_RENDER`, and copies the
resulting framebuffer directly into Blender's `RenderResult` — observed
working through a real `F12` keypress in the actual Blender GUI (via WSLg),
not only in `--background` mode. See `docs/evidence/phase05/` for full
evidence, including the GUI screenshot, and
`docs/evidence/phase05/sphere-light-investigation/` for a real MoonRay-side
lighting anomaly found and worked around during this phase.

## Delivered
- `addon/__init__.py` — `bl_info` and `register()`/`unregister()`
  orchestration.
- `addon/engine.py` — `MoonRayRenderEngine(bpy.types.RenderEngine)`:
  `bl_idname = "MOONRAY"`, `render()` implementing the full
  translate → launch → CREATE_SCENE → START_RENDER → RenderResult pipeline
  with cancellation checkpoints (`test_break()`) and typed exception handling
  covering scene-translation errors, bridge-launch failures, bridge
  protocol errors, and bridge-crash/connection-loss, each reported via
  `self.report`/`self.error_set` without raising out of `render()`.
- `addon/scene_writer.py` — minimal Blender depsgraph → RDL2 ASCII (`.rdla`)
  translator: validates the scene fits Phase 05's supported shape (exactly
  one perspective camera, one mesh, one point light), triangulates and
  world-transforms the mesh, converts Blender's Z-up coordinate frame to
  RDL2/MoonRay's Y-up frame, maps the camera's focal length/sensor
  width/clip planes, and approximates the point light as an axis-snapped
  `DistantLight` (see "Decisions made" below).
- `addon/bridge_launcher.py` — one-shot `moonray_bridge` process
  lifecycle: launch with the required `RDL2_DSO_PATH`/`REZ_MOONRAY_ROOT`
  env vars, wait for its socket (generous timeout per Phase 04's documented
  cold-start variance), complete the `HELLO` handshake, and guarantee
  cleanup (`BridgeHandle.shutdown()`, always called from `engine.py`'s
  `finally`) regardless of success, cancellation, or failure.
- `addon/bridge_client.py` — the add-on's own production copy of the wire
  client (`docs/bridge/MESSAGE_SCHEMA.md` envelope), adapted from
  `bridge/client/bridge_client.py` per `NEXT_SESSION.md`'s stated intent;
  fixes a leftover connect-timeout bug found during this phase's evidence
  gathering (see completion record below).
- `addon/properties.py` / `addon/panels.py` — `scene.moonray` settings
  (`pixel_samples`, `bridge_binary_path` override) and a Render Properties
  panel, plus making the stock Output/Dimensions panels visible for the
  `MOONRAY` engine (hidden by Blender by default for custom engines).
- `docs/evidence/phase05/` — GUI and background-mode render evidence, error-
  path evidence, the generated example `.rdla`, and a full investigation
  record of the SphereLight/DistantLight anomaly found in this MoonRay
  build.

## Observed verification
| Check | Result |
|---|---|
| `MoonRay` is selectable in Render Engine menu | PASS |
| Baseline `.blend` (factory-default Cube/Camera/Light) renders with F12 via MoonRay | PASS — real `F12` keypress in the real Blender GUI via WSLg, `docs/evidence/phase05/f12-gui-render.png` |
| Render result appears inside Blender without a manual external render step | PASS — `RenderResult` populated directly, no file round-trip |
| Cancel does not leave zombie bridge/render | PASS — `bridge_launcher.BridgeHandle.shutdown()` unconditional in `engine.py`'s `finally`; zero lingering `moonray_bridge` processes observed after every test in this phase |
| Bridge failure is reported without taking Blender down | PASS — nonexistent-binary and unsupported-scene cases both produce a clean, catchable `RuntimeError` from `bpy.ops.render.render()` (Blender's standard `error_set()` propagation, not a crash) and Blender remains fully responsive afterward |
| Verify Blender 5.2 RenderEngine API from official source | PASS — grounded via live introspection of the pinned 5.2.1 build's own `bpy.types.RenderEngine.bl_rna` (functions and properties), not assumed from training data or docs alone |

## Decisions made

### Light translation: `DistantLight`, axis-snapped, not a direct `SphereLight` mapping
The natural translation of Blender's default `POINT` light is RDL2's
`SphereLight`. End-to-end testing (`docs/evidence/phase05/sphere-light-investigation/`)
found that `SphereLight` reproducibly fails to illuminate an
`RdlMeshGeometry` authored by this module's own vertex-authoring code path
in this pinned MoonRay build — camera-visible faces render flat black —
across a wide sweep of positions, distances, radii, intensities and
`normalized` settings, while the identical geometry shades correctly under
both `EnvLight` and an axis-aligned `DistantLight`. A second, independent
anomaly was found on top of it: even `DistantLight` fails the same way for a
non-axis-aligned (but mathematically verified orthonormal, correctly
oriented, right-handed) `node_xform`. Root-causing either at the MoonRay
engine/build level is outside Phase 05's explicit scope ("ONLY minimal
translation of one baseline scene", not an engine bug hunt). The shipped
workaround — approximate the point light as a `DistantLight` aimed from its
position toward the primitive's centroid, then snap that direction to the
nearest world axis — was verified end-to-end to shade the translated
baseline scene correctly and is what produced the accepted F12 evidence.
Point-light photometry (falloff, radius, exact position) is explicitly not
matched; revisit when lights are translated generally (Phase 06/07) or if
this MoonRay build's anomaly is otherwise root-caused.

### Bridge lifecycle: one-shot per render, not a persistent long-lived process
`bridge_launcher.launch_and_connect()` starts a fresh `moonray_bridge` for
every `render()` call and tears it down in `finally`, rather than keeping one
running across renders. This matches Phase 04's "one client connection at a
time" bridge design and keeps Phase 05's failure/cancellation handling simple
(a crashed or stuck bridge only ever affects the render in progress).
Persistent-bridge lifecycle, restart policy and reconnection are Phase 11
scope (`docs/bridge/LIFECYCLE.md` "Auto-restart/backoff policy after crash" —
Open).

### `CREATE_SCENE` still takes a full `.rdla` file path — protocol not extended
Per `NEXT_SESSION.md`'s option (a), the add-on writes a self-contained
`.rdla` file per render and passes its path to the existing Phase 04
`CREATE_SCENE` contract unchanged, rather than extending the bridge message
schema with a canonical scene-object payload. `docs/bridge/MESSAGE_SCHEMA.md`'s
"Open — Phase 04/06/07" per-message payload field layout remains open for
Phase 06 to decide when general (not just baseline) scene translation is
implemented.

## Problems discovered and fixed
1. **`SphereLight`/non-axis-aligned `DistantLight` illumination anomaly** —
   see "Decisions made" above and the full investigation record.
2. **`BridgeClient` leftover connect-timeout misreported an in-progress
   render as a bridge crash.** `socket.settimeout(connect_timeout)` in
   `addon/bridge_client.py.__init__` was never cleared after `connect()`
   succeeded, so it silently bounded every subsequent `recv()` too —
   including the blocking wait for `START_RENDER`'s response, which can
   legitimately exceed 5 seconds (observed: tens of seconds at 640×480/32
   samples). This was caught live during GUI evidence-gathering: a real,
   successful, still-in-progress render was reported to the user as "MoonRay:
   bridge connection lost (process crash?): timed out". Fixed by clearing the
   timeout (`settimeout(None)`, i.e. blocking) immediately after `connect()`
   succeeds — a genuine crash still surfaces correctly (the connection
   actually drops), only the false-positive-from-a-slow-render case is
   removed.
3. **`RenderPass.rect` shape.** Blender's `RenderPass.rect` setter expects a
   sequence of `(width*height)` per-pixel `(channels,)`-tuples, not one flat
   list of `width*height*channels` floats (`TypeError: expected a sequence
   of float, not float` on first attempt). Fixed in
   `addon/engine.py::_write_result`.
4. **GUI-automation-only issues, not product defects** — see
   `docs/evidence/phase05/README.md` "GUI automation notes": `INVOKE_DEFAULT`
   from a `bpy.app.timers` callback silently no-ops (no window/area context);
   Windows-side synthetic input was unreliable against the WSLg-forwarded
   window and `xdotool` (installed into the distro) was used instead to
   reliably deliver a real `F12` keypress to the X11 window directly.

## Deviations / technical debt
- Point-light photometry (Watts-accurate falloff, radius, true point-light
  behavior) is not matched — the `DistantLight` approximation is a pragmatic,
  documented simplification (see `addon/scene_writer.py` module docstring),
  not a claim of physical accuracy. Revisit in Phase 06/07 (general light
  translation) or sooner if the underlying MoonRay anomaly is root-caused.
- The SphereLight/non-axis-aligned-DistantLight anomaly itself remains
  unexplained at the engine level; no upstream report filed yet.
- `addon/engine.py` writes a last-resort traceback to a fixed path
  (`/tmp/moonray_addon_last_error.log`) for any exception type not already
  classified — a debugging aid added during this phase's own evidence-
  gathering, left in as a reasonable defensive measure, not part of any
  acceptance criterion.
- Camera translation uses Blender's `sensor_fit = AUTO` semantics
  approximately (mapping `sensor_width`/`lens` straight through to
  `film_width_aperture`/`focal`); exact FOV parity across non-square aspect
  ratios is not verified. Acceptable for Phase 05's baseline-scene scope.
- No Rendered Viewport, no general material/geometry translation, no
  AOVs/animation — all explicitly out of Phase 05 scope per
  `docs/phases/05-blender-renderengine-integration.md`.

## Architectural impact
None. ADR-0002 (Direct Bridge primary) and ADR-0004 (bridge transport/wire
format) are unaffected — Phase 05 is a pure consumer of the existing,
unmodified Phase 04 bridge protocol and binary. No ADR added or amended.

## GPU/XPU status carried forward
Unchanged from Phase 03/04: CPU is the only proven render path.

## Follow-up
Phase 06: geometry, transforms, camera and lights translation — this is
where the SphereLight/DistantLight anomaly and point-light photometry
approximation should be revisited with more room to investigate, and where
`CREATE_SCENE`'s raw-`.rdla`-path contract is expected to be replaced by a
canonical bridge scene schema. Not started by this phase.
