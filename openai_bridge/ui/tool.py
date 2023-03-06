import bpy

from ..op.image import OPENAI_OT_GeneateImage
from ..op.chat import OPENAI_OT_Chat


class OPENAI_WST_OpenAIImageTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_image_tool"
    bl_label = "OpenAI Image Tool"
    bl_description = "Image tools that uses OpenAI API"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_keymap = (
        (
            OPENAI_OT_GeneateImage.bl_idname,
            {"type": 'G', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_GeneateImage.bl_idname)
        layout.prop(props, "num_images")
        layout.prop(props, "image_size")


class OPENAI_WST_OpenAIChatTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_chat_tool"
    bl_label = "OpenAI Chat Tool"
    bl_description = "Chat tools that uses OpenAI API"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_keymap = (
        (
            OPENAI_OT_Chat.bl_idname,
            {"type": 'C', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_Chat.bl_idname)
        layout.prop(props, "text_name")
