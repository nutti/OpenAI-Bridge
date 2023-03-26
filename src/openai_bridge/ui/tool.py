import bpy

from ..op.image import OPENAI_OT_GeneateImage
from ..op.audio import OPENAI_OT_TranscribeAudio
from ..op.chat import OPENAI_OT_Chat
from ..op.code import OPENAI_OT_Code
from ..utils.common import ICON_DIR


class OPENAI_WST_OpenAIImageTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_image_tool"
    bl_label = "OpenAI Image Tool"
    bl_description = "Image tools"
    bl_space_type = 'IMAGE_EDITOR'
    bl_context_mode = 'VIEW'
    bl_icon = f"{ICON_DIR}/custom.openai_image"

    bl_keymap = (
        (
            OPENAI_OT_GeneateImage.bl_idname,
            {"type": 'SPACE', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")


class OPENAI_WST_OpenAIAudioTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_audio_tool"
    bl_label = "OpenAI Audio Tool"
    bl_description = "Audio tools"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_context_mode = 'SEQUENCER'
    bl_icon = f"{ICON_DIR}/custom.openai_audio"

    bl_keymap = (
        (
            OPENAI_OT_TranscribeAudio.bl_idname,
            {"type": 'SPACE', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")


class OPENAI_WST_OpenAIChatTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_chat_tool"
    bl_label = "OpenAI Chat Tool"
    bl_description = "Chat tools"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_icon = f"{ICON_DIR}/custom.openai_chat"

    bl_keymap = (
        (
            OPENAI_OT_Chat.bl_idname,
            {"type": 'SPACE', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_Chat.bl_idname)
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")

        layout.separator()

        layout.prop(props, "num_conditions")


class OPENAI_WST_OpenAICodeTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_code_tool"
    bl_label = "OpenAI Code Tool"
    bl_description = "Code tools"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_icon = f"{ICON_DIR}/custom.openai_chat"

    bl_keymap = (
        (
            OPENAI_OT_Code.bl_idname,
            {"type": 'SPACE', "value": 'PRESS'},
            {},
        ),
    )

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_Code.bl_idname)
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(props, "sync")

        layout.separator()

        layout.prop(prefs, "code_tool_model")
        layout.prop(props, "num_conditions")
        layout.prop(props, "execute_immediately")
