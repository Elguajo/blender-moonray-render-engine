"""MoonRay Render Properties panel, plus making the relevant stock Blender
panels (output path, dimensions) visible for the MOONRAY engine -- otherwise
Blender hides them for any custom RenderEngine by default."""
import bpy

_STOCK_PANEL_IDS = (
    "RENDER_PT_context_output",
    "RENDER_PT_dimensions",
    "RENDER_PT_output",
)


class RENDER_PT_moonray_settings(bpy.types.Panel):
    bl_label = "MoonRay"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    COMPAT_ENGINES = {'MOONRAY'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout
        settings = context.scene.moonray
        layout.prop(settings, "pixel_samples")
        layout.prop(settings, "bridge_binary_path")


classes = (RENDER_PT_moonray_settings,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for panel_id in _STOCK_PANEL_IDS:
        panel = getattr(bpy.types, panel_id, None)
        if panel is not None and hasattr(panel, "COMPAT_ENGINES"):
            panel.COMPAT_ENGINES.add('MOONRAY')


def unregister():
    for panel_id in _STOCK_PANEL_IDS:
        panel = getattr(bpy.types, panel_id, None)
        if panel is not None and hasattr(panel, "COMPAT_ENGINES"):
            panel.COMPAT_ENGINES.discard('MOONRAY')
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
