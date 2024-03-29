import bpy

from ..op.image import (
    OPENAI_OT_GeneateImage,
    OPENAI_OT_EditImage,
)
from ..op.audio import OPENAI_OT_TranscribeSoundStrip
from ..op.chat import OPENAI_OT_Chat
from ..op.code import (
    OPENAI_OT_GenerateCode,
    OPENAI_OT_GenerateCodeFromAudio,
)
from ..utils.common import ICON_DIR


class OPENAI_WST_ImageTool(bpy.types.WorkSpaceTool):

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
        (
            OPENAI_OT_EditImage.bl_idname,
            {"type": 'E', "value": 'PRESS'},
            {},
        ),
    )

    # pylint: disable=E0213
    def draw_settings(context, layout, _):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")


class OPENAI_WST_AudioTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_audio_tool"
    bl_label = "OpenAI Audio Tool"
    bl_description = "Audio tools"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_context_mode = 'SEQUENCER'
    bl_icon = f"{ICON_DIR}/custom.openai_audio"

    bl_keymap = (
        (
            OPENAI_OT_TranscribeSoundStrip.bl_idname,
            {"type": 'SPACE', "value": 'PRESS'},
            {},
        ),
    )

    # pylint: disable=E0213
    def draw_settings(context, layout, _):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")


class OPENAI_WST_ChatTool(bpy.types.WorkSpaceTool):

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

    # pylint: disable=E0213
    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_Chat.bl_idname)
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")

        layout.separator()

        layout.prop(props, "num_conditions")


class OPENAI_WST_CodeTool(bpy.types.WorkSpaceTool):

    bl_idname = "openai.openai_code_tool"
    bl_label = "OpenAI Code Tool"
    bl_description = "Code tools"
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_icon = f"{ICON_DIR}/custom.openai_code"

    bl_keymap = (
        (
            OPENAI_OT_GenerateCode.bl_idname,
            {"type": 'SPACE', "value": 'PRESS'},
            {"properties": [("execute_immediately", True)]},
        ),
        (
            OPENAI_OT_GenerateCodeFromAudio.bl_idname,
            {"type": 'A', "value": 'PRESS', "shift": True},
            {},
        ),
    )

    # pylint: disable=E0213
    def draw_settings(context, layout, tool):
        props = tool.operator_properties(OPENAI_OT_GenerateCode.bl_idname)
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        layout.prop(prefs, "async_execution")

        layout.separator()

        layout.prop(props, "num_conditions")
        audio_props = tool.operator_properties(
            OPENAI_OT_GenerateCodeFromAudio.bl_idname)
        audio_props.num_conditions = props.num_conditions
