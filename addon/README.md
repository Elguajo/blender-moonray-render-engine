# `addon/`

Blender 5.2+ MoonRay Render Engine add-on.

Phase 05 delivered: RenderEngine registration (`engine.py`), settings/UI
(`properties.py`, `panels.py`), a minimal baseline-scene translator
(`scene_writer.py`), Bridge Process launch/lifecycle (`bridge_launcher.py`)
and its wire client (`bridge_client.py`), and F12/RenderResult integration —
verified end-to-end through a real `F12` keypress in the Blender GUI, see
`docs/completions/05-blender-renderengine-integration.md` and
`docs/evidence/phase05/`.

Still open for later phases: general (not just baseline) depsgraph
translation orchestration and incremental updates (Phase 06/07), Rendered
Viewport presentation (Phase 08), AOV/pass integration (Phase 09).
