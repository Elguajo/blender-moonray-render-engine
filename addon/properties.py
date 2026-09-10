"""Minimal MoonRay render settings (docs/phases/05-blender-renderengine-integration.md
"Implement engine registration and settings panel")."""
import bpy


class MoonRaySettings(bpy.types.PropertyGroup):
    bridge_binary_path: bpy.props.StringProperty(
        name="Bridge Binary",
        description=(
            "Path to the moonray_bridge executable. Leave empty to use the "
            "Phase 06 build default (scripts/linux/phase06_build_bridge.sh)"
        ),
        subtype='FILE_PATH',
        default="",
    )
    pixel_samples: bpy.props.IntProperty(
        name="Pixel Samples",
        description="MoonRay SceneVariables pixel_samples for this render",
        default=16,
        min=1,
        max=4096,
    )


classes = (MoonRaySettings,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.moonray = bpy.props.PointerProperty(type=MoonRaySettings)


def unregister():
    del bpy.types.Scene.moonray
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
