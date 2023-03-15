import bpy

from ..op.image import OPENAI_OT_GeneateImage
from ..op.audio import OPENAI_OT_TranscriptAudio
from ..op.chat import OPENAI_OT_Chat
from ..utils.common import ICON_DIR


class OPENAI_WST_OpenAIImageTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_image_tool"
    bl_label = "OpenAI Image Tool"
    bl_description = "Image tools that uses OpenAI API"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_icon = f"{ICON_DIR}/custom.openai_image"

    bl_keymap = (
        (
            OPENAI_OT_GeneateImage.bl_idname,
            {"type": 'G', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_GeneateImage.bl_idname)

        layout.prop(props, "sync")

        layout.separator()

        layout.prop(props, "num_images")
        layout.prop(props, "image_size")


class OPENAI_WST_OpenAIAudioTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_audio_tool"
    bl_label = "OpenAI Audio Tool"
    bl_description = "Audio tools that uses OpenAI API"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_icon = f"{ICON_DIR}/custom.openai_audio"

    bl_keymap = (
        (
            OPENAI_OT_TranscriptAudio.bl_idname,
            {"type": 'T', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        sc = context.scene
        props = tool.operator_properties(OPENAI_OT_TranscriptAudio.bl_idname)

        layout.prop(props, "sync")

        layout.separator()

        layout.prop(props, "display_target")
        if props.display_target == 'TEXT_EDITOR':
            layout.prop(sc, "openai_audio_target_text", text="Text")
        elif props.display_target == 'TEXT_OBJECT':
            layout.prop(sc, "openai_audio_target_text_object", text="Object")

        layout.separator()

        layout.prop(props, "temperature")
        layout.prop(props, "language")


class OPENAI_WST_OpenAIChatTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_chat_tool"
    bl_label = "OpenAI Chat Tool"
    bl_description = "Chat tools that uses OpenAI API"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_icon = f"{ICON_DIR}/custom.openai_chat"

    bl_keymap = (
        (
            OPENAI_OT_Chat.bl_idname,
            {"type": 'C', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_Chat.bl_idname)

        layout.prop(props, "sync")

        layout.separator()

        layout.prop(props, "new_topic")
        if props.new_topic:
            layout.prop(props, "new_topic_name")
        else:
            layout.prop(props, "topic")

        layout.separator()

        layout.prop(props, "num_conditions")
