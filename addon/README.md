# `addon/`

Blender 5.2+ MoonRay Render Engine add-on.

Phase 05 delivered: RenderEngine registration (`engine.py`), settings/UI
(`properties.py`, `panels.py`), Bridge Process launch/lifecycle
(`bridge_launcher.py`) and its wire client (`bridge_client.py`), and
F12/RenderResult integration — verified end-to-end through a real `F12`
keypress in the Blender GUI, see
`docs/completions/05-blender-renderengine-integration.md` and
`docs/evidence/phase05/`.

Phase 06 replaced Phase 05's one-mesh/one-light baseline translator
(`scene_writer.py`, which wrote a self-contained `.rdla` text file) with the
general `scene_translator.py`: any number of mesh objects, native Blender
light-type mapping (`POINT`/`SUN`/`SPOT`/`AREA` → `Sphere`/`Distant`/`Spot`/
`Rect`/`DiskLight`, `ELLIPSE` shape fails explicitly), the confirmed camera
unit mapping, and per-object visibility flags — sent over the structured
bridge protocol (`docs/bridge/SCENE_TRANSLATION.md`, ADR-0005) instead of a
round-tripped `.rdla` file. `bridge_client.py` gained `update_object()`/
`update_camera()`; `protocol_version` is now 2. See
`docs/completions/06-geometry-camera-lights.md` and `docs/evidence/phase06/`.

Still open for later phases: material/texture translation and instancing
(Phase 07), Rendered Viewport presentation with real incremental
add/update/delete across a live bridge session (Phase 08 — Phase 06 proved
the wire-level update/delete semantics work, `bridge/tests/run_phase06_tests.py`,
but the add-on itself still launches one fresh bridge process per render and
always sends a full `create`), AOV/pass integration (Phase 09).
