# Phase 05 Evidence — Blender RenderEngine Integration and First F12 Frame

Observed 2026-09-10 inside the `MoonRay-Rocky9` WSL2 distro, against the
Phase 04 `moonray_bridge` binary (`bridge/build/bridge04/moonray_bridge`,
unmodified by this phase) and Blender 5.2.1 LTS (`/root/moonray-blender/tools/blender-current/blender`),
both GUI (via WSLg) and `--background` mode.

## Files

- [`f12-gui-render.png`](f12-gui-render.png) — **primary acceptance
  evidence**: a full desktop screenshot (captured on the Windows host,
  `System.Drawing`/`CopyFromScreen`, not a cropped/composited image) of the
  real Blender GUI, running via WSLg, immediately after an `F12` keypress
  sent to the actual Blender X11 window with `xdotool key --window <id> F12`
  (installed for this purpose; `key --window` targets the X11 window
  directly rather than relying on Windows-side synthetic input reaching the
  WSLg-forwarded window, which proved unreliable — see "GUI automation
  notes" below). The Outliner shows the default `Cube`/`Camera`/`Light`
  scene with `MoonRay` selected as the active Render Engine (visible via the
  MoonRay panel having been used to set it up beforehand); the `Blender
  Render` window shows `Frame:1 | Time:00:55.30 | Mem:28M, Peak:36M` (a
  clean completion status, no error text) and the correctly shaded MoonRay
  render of the cube (bright top face toward the light, correctly dark side
  faces).
- [`background-mode-addon-render.png`](background-mode-addon-render.png) —
  the same add-on package (`addon/`, loaded via `bpy.utils.register_class`
  exactly as Blender's own add-on installer would), driven through
  `bpy.ops.render.render(write_still=False)` in `--background` mode, with
  the result read back via `Image.save_render()`. Confirms the pipeline
  independent of any GUI-automation concern.
- [`error-paths-run.txt`](error-paths-run.txt) — two clean-failure checks
  run against the real add-on and a real (failed-to-start or
  scope-rejected) render: a nonexistent bridge binary path, and a scene with
  two mesh objects (outside Phase 05's "exactly one primitive" scope). Both
  report a clean `RuntimeError` from `bpy.ops.render.render()` (Blender's own
  standard behavior when `RenderEngine.error_set()` is called — not a crash)
  and Blender remains fully responsive afterward (proven by successfully
  running a further, unrelated operator in the same session).
- [`example-generated-scene.rdla.txt`](example-generated-scene.rdla.txt) — the
  actual `.rdla` text `addon/scene_writer.py` produced for Blender's
  factory-default scene (Cube + Camera + Light), as sent to the bridge's
  `CREATE_SCENE` (`.txt` suffix only to bypass the repo's blanket
  `*.rdla`/`*.rdlb` gitignore rule for generated scene files — this one is
  evidence, not a rebuildable artifact).
- [`diagnostic-envlight-works.png`](diagnostic-envlight-works.png),
  [`diagnostic-spherelight-reference-scene.png`](diagnostic-spherelight-reference-scene.png)
  — two of the diagnostic renders from the light-translation investigation;
  full account in [`sphere-light-investigation/README.md`](sphere-light-investigation/README.md).

## Observed verification

| Check | Result |
|---|---|
| `MoonRay` registers and is selectable as a Render Engine | PASS — `addon/panels.py`/`addon/engine.py`, observed both via `scene.render.engine = 'MOONRAY'` succeeding and via the GUI's own Render Properties engine dropdown during the F12 test |
| Baseline `.blend` (factory-default Cube/Camera/Light) renders via F12 through MoonRay | PASS — `f12-gui-render.png`, real `F12` keypress in the real GUI |
| Render result appears inside Blender without a manual external render step | PASS — same evidence; `RenderResult.layers[0].passes["Combined"].rect` populated directly by `addon/engine.py`, no file round-trip |
| MoonRay backend (not a stub/passthrough) actually produced the pixels | PASS — the rendered image is the physically correct MoonRay/DwaBaseMaterial shading result (bright face toward the light source, dark faces away from it), matches the geometry/light actually described in `example-generated-scene.rdla`, and the bridge log for each run shows real `moonray::rndr::RenderContext` scene load + batch render messages (`Loading Scene File(s)`, `Render prep time`, `Render time`) |
| Cancel does not leave a zombie bridge/render | PASS (by construction + observed) — `bridge_launcher.BridgeHandle.shutdown()` runs unconditionally in `engine.py`'s `finally` block; `ps aux \| grep moonray_bridge` showed zero lingering processes after every test run in this phase, including the deliberately-failed ones |
| Bridge failure is reported without taking Blender down | PASS — `error-paths-run.txt`; also incidentally exercised for real during evidence-gathering when a leftover socket timeout (see "Bugs found and fixed" below) surfaced as `bridge_client.BridgeError`-style connection-lost text, reported cleanly via `self.report`/`self.error_set`, with Blender remaining fully interactive afterward |

## Bugs found and fixed during evidence-gathering

1. **`SphereLight` / non-axis-aligned `DistantLight` illumination anomaly.**
   Full investigation in
   [`sphere-light-investigation/README.md`](sphere-light-investigation/README.md).
   Not a bug in code written this phase — an anomaly in this pinned MoonRay
   build, worked around by using an axis-snapped `DistantLight` instead of a
   direct `SphereLight` translation.
2. **`BridgeClient`'s connect-timeout leaked into the render-wait.**
   `addon/bridge_client.py`'s socket carried its 5-second `connect_timeout`
   as the *ongoing* socket timeout after `connect()` succeeded, because
   `socket.settimeout()` applies to all future operations, not just the call
   it was set before. `START_RENDER`'s response can legitimately take longer
   than 5 seconds (observed: several seconds at low resolution, tens of
   seconds at 640x480/32 samples on this machine), so a real, successful,
   in-progress render was misreported as a bridge crash
   (`ConnectionError`/`OSError`, surfaced as "bridge connection lost
   (process crash?): timed out") purely from this leftover timeout — observed
   directly during GUI evidence-gathering. Fixed by calling
   `self._sock.settimeout(None)` immediately after `connect()` succeeds
   (blocking reads thereafter; the bridge process either responds or the
   connection actually drops, which still surfaces correctly as a crash).
3. **`RenderPass.rect` assignment shape.** A first attempt assigned a flat
   `list` of `w*h*channels` floats; Blender's API requires a sequence of
   `(w*h)` per-pixel `channels`-tuples instead (`TypeError: expected a
   sequence of float, not float`). Fixed in `addon/engine.py::_write_result`.

## GUI automation notes (not a product defect)

Getting a literal on-screen "F12 pressed" screenshot required more than one
attempt, entirely due to the automation tooling used to drive/observe the
WSLg-hosted Blender window from this session, not the add-on itself:
- `bpy.ops.render.render('INVOKE_DEFAULT')` called from inside a
  `bpy.app.timers` callback (used for an early, scripted attempt) does not
  get the window/area context a real UI-triggered invocation has, and
  silently no-ops (no exception, `Render Result` stays `(0, 0)`). Using the
  operator's default execution context instead
  (`bpy.ops.render.render(write_still=False)`) works correctly from a timer
  and was used for `background-mode-addon-render.png`-equivalent GUI checks.
- Windows-side synthetic mouse clicks and key presses (via this session's
  desktop-automation tool) landed inconsistently on the WSLg-forwarded
  Blender window (menu items not receiving clicks at their visually-read
  coordinates; `F12`/`Escape` not reaching the window at all). Installing
  `xdotool` in the WSL distro and sending `windowactivate`/`click`/`key`
  directly to the X11 window id (native X11 protocol, not a Windows input
  event translated through WSLg) was reliable and is what produced
  `f12-gui-render.png`.
