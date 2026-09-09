# `bridge/`

Future native `moonray_bridge` implementation lives here.

Current architecture: separate local C++ process hosting MoonRay/scene_rdl2 and exposing a versioned local control + bulk-data boundary to Blender.

No placeholder implementation is committed yet because Phase 03 must first prove the pinned native MoonRay runtime and Phase 04 owns the actual bridge/protocol decisions.
