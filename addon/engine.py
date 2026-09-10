"""MoonRay bpy.types.RenderEngine integration (Phase 05).

Scope (docs/phases/05-blender-renderengine-integration.md): register the
engine, launch/version-check the bridge, translate the one supported baseline
scene, run one final (F12) render through the Direct Bridge, and copy the
result into Blender's Render Result -- no Rendered Viewport (Phase 08), no
general material/geometry translation (Phase 06/07).
"""
from __future__ import annotations

import os
import shutil
import tempfile

import bpy

from . import bridge_client
from . import bridge_launcher
from . import scene_writer


class MoonRayRenderEngine(bpy.types.RenderEngine):
    bl_idname = "MOONRAY"
    bl_label = "MoonRay"
    bl_use_preview = False  # Rendered Viewport is Phase 08 scope.
    bl_use_gpu_context = False

    def render(self, depsgraph):
        scene = depsgraph.scene
        width = self.resolution_x
        height = self.resolution_y
        pixel_samples = max(int(getattr(scene.moonray, "pixel_samples", 16)), 1)
        bridge_bin = getattr(scene.moonray, "bridge_binary_path", "") or None

        result = self.begin_result(0, 0, width, height)
        cancelled = False
        run_dir = tempfile.mkdtemp(prefix="moonray_blender_render_")
        try:
            if self.test_break():
                cancelled = True
                return

            rdla_path = os.path.join(run_dir, "scene.rdla")
            scene_writer.write_scene(
                depsgraph, rdla_path,
                image_width=width, image_height=height, pixel_samples=pixel_samples,
            )

            if self.test_break():
                cancelled = True
                return

            handle = bridge_launcher.launch_and_connect(bridge_bin=bridge_bin, log_dir=run_dir)
            try:
                if self.test_break():
                    cancelled = True
                    return

                handle.client.create_scene(rdla_path)

                if self.test_break():
                    cancelled = True
                    return

                # START_RENDER is a single synchronous call in the Phase 04
                # bridge protocol (no STOP_RENDER support yet -- explicit
                # ERROR category 2 NOT_IMPLEMENTED_PHASE04, per
                # docs/completions/04-direct-bridge-prototype.md); a cancel
                # requested while this call is in flight can only be honored
                # once it returns, by discarding the result -- see class
                # docstring and docs/bridge/LIFECYCLE.md "Render-mode
                # lifecycle" (cancellation semantics are refined in Phase 09).
                reply = handle.client.start_render("final")
                if self.test_break():
                    cancelled = True
                    return
                self._write_result(result, reply["payload"])
            finally:
                handle.shutdown()
        except scene_writer.SceneTranslationError as exc:
            self.report({'ERROR'}, f"MoonRay: scene not supported: {exc}")
            self.error_set(str(exc))
        except bridge_launcher.BridgeLaunchError as exc:
            self.report({'ERROR'}, f"MoonRay: bridge failed to start: {exc}")
            self.error_set(str(exc))
        except bridge_client.BridgeError as exc:
            self.report({'ERROR'}, f"MoonRay: render failed: {exc}")
            self.error_set(str(exc))
        except (ConnectionError, OSError) as exc:
            # ERROR_MODEL.md category 4: bridge process crash detected as a
            # broken connection. Must not take Blender down.
            self.report({'ERROR'}, f"MoonRay: bridge connection lost (process crash?): {exc}")
            self.error_set(str(exc))
        except Exception as exc:  # noqa: BLE001 - last-resort guard, see comment
            # Anything not already classified above must still be reported
            # cleanly rather than escape render() and destabilize Blender
            # (ARCHITECTURE.md failure isolation). Also persists a traceback
            # to a fixed path for post-mortem debugging since GUI-mode
            # stdout is not reliably visible/flushed.
            import traceback
            self.report({'ERROR'}, f"MoonRay: unexpected internal error: {exc}")
            self.error_set(str(exc))
            try:
                with open("/tmp/moonray_addon_last_error.log", "w") as f:
                    f.write(traceback.format_exc())
            except OSError:
                pass
        finally:
            self.end_result(result, cancel=cancelled)
            shutil.rmtree(run_dir, ignore_errors=True)

    def _write_result(self, result, render_complete_payload: dict) -> None:
        stats = render_complete_payload
        w, h, channels = stats["width"], stats["height"], stats["channels"]
        buf = bridge_client.read_framebuffer_f32(stats["shm_name"], w, h, channels)

        # RDL2's RenderBuffer (docs/bridge/FRAMEBUFFER_PROTOCOL.md: interleaved
        # RGBA float32) is stored top-to-bottom; Blender's RenderPass.rect
        # expects bottom-to-top scanline order, so rows are reversed here.
        # RenderPass.rect additionally expects a sequence of per-pixel
        # (channels,)-float tuples, shape (w*h, channels) -- not one flat
        # list of w*h*channels floats.
        row_len = w * channels
        pixels: list = []
        for row in range(h - 1, -1, -1):
            start = row * row_len
            row_slice = buf[start:start + row_len]
            for px_start in range(0, row_len, channels):
                pixels.append(tuple(row_slice[px_start:px_start + channels]))

        render_layer = result.layers[0]
        render_layer.passes["Combined"].rect = pixels


def register():
    bpy.utils.register_class(MoonRayRenderEngine)


def unregister():
    bpy.utils.unregister_class(MoonRayRenderEngine)
