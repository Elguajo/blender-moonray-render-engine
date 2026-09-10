"""Phase 06 background-mode Blender evidence script. Run with:
blender --background --python this_file.py

Registers addon/ exactly as Blender's own installer would (bpy.utils.register_class
via addon.register()), builds a scene beyond Phase 05's single-object baseline
(two mesh objects + a SUN light, to exercise Phase 06's new multi-object
translation and native Blender light-type mapping), points MoonRay at it, and
renders through the real RenderEngine.render() path into a PNG.
"""
import sys
import os

REPO_ROOT = "/mnt/d/01_DEV/blender-moonray-render-engine"
sys.path.insert(0, REPO_ROOT)

import bpy  # noqa: E402

import addon  # noqa: E402

addon.register()

scene = bpy.context.scene

# Remove Blender's factory-default objects so we build a known scene.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Object 1: default cube at origin.
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
cube = bpy.context.active_object
cube.name = "TestCube"

# Object 2 (Phase 06 new capability: more than one mesh): a second cube,
# offset to the side.
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.0, 0.0, 0.0))
cube2 = bpy.context.active_object
cube2.name = "TestCube2"

# Light: SUN (Phase 06 new capability: native type mapping, not Phase 05's
# hardcoded POINT-as-Distant-workaround), pointed mostly downward.
bpy.ops.object.light_add(type='SUN', location=(0.0, 0.0, 5.0))
light = bpy.context.active_object
light.data.energy = 3.0
light.rotation_euler = (0.3, 0.2, 0.0)  # a non-axis-aligned tilt, on purpose

# Camera.
bpy.ops.object.camera_add(location=(4.0, -6.0, 3.0), rotation=(1.1, 0.0, 0.6))
cam = bpy.context.active_object
scene.camera = cam

scene.render.engine = 'MOONRAY'
scene.render.resolution_x = 320
scene.render.resolution_y = 240
scene.moonray.pixel_samples = 16
scene.moonray.bridge_binary_path = "/root/moonray-blender/build/bridge06/moonray_bridge"

out_path = "/root/moonray-blender/logs/phase06-build/background-render.png"
scene.render.filepath = out_path
scene.render.image_settings.file_format = 'PNG'

bpy.ops.render.render(write_still=True)

print(f"PHASE06_BLENDER_RENDER_OK -- wrote {out_path}")
