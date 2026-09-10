"""MoonRay Render Engine add-on for Blender 5.2+ (Phase 05: RenderEngine
registration, minimal settings panel, bridge launch/version-check, minimal
baseline-scene translation, F12 final render into Blender's Render Result).

See docs/phases/05-blender-renderengine-integration.md for scope and
docs/completions/05-blender-renderengine-integration.md for what was
actually verified.
"""
bl_info = {
    "name": "MoonRay Render Engine",
    "author": "blender-moonray-render-engine project",
    "version": (0, 5, 0),
    "blender": (5, 2, 0),
    "location": "Render Properties > Render Engine",
    "description": "Direct MoonRay Bridge render engine integration (Phase 05: F12 final render only)",
    "category": "Render",
}

from . import properties
from . import panels
from . import engine

_modules = (properties, panels, engine)


def register():
    for m in _modules:
        m.register()


def unregister():
    for m in reversed(_modules):
        m.unregister()
