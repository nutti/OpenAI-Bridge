import bpy

from ..utils.bl_class_registry import BlClassRegistry


@BlClassRegistry()
class WM_MT_button_context(bpy.types.Menu):

    bl_label = "OpenAI"

    def draw(self, context):
        pass
