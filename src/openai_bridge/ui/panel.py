import glob
import os
import bpy

from ..op import image
from ..op import audio
from ..op import chat
from ..op import code
from ..utils.common import (
    ChatTextFile,
    parse_response_data,
    CODE_DATA_DIR,
    draw_data_on_ui_layout,
)
from ..utils import error_storage


class OPENAI_PT_ImageTool(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Image Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout
        icon_collection = sc.openai_icon_collection["openai_base"]

        layout.label(text="", icon_value=icon_collection.icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_ImageToolGenerateImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generate Image"
    bl_parent_id = "OPENAI_PT_ImageTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='CONSOLE')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_generate_image_props

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        ops = row.operator(
            image.OPENAI_OT_GeneateImage.bl_idname, icon='PLAY', text="")
        ops.prompt = props.prompt
        ops.num_images = props.num_images
        ops.image_size = props.image_size
        ops.auto_image_name = props.auto_image_name
        ops.image_name = props.image_name

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Size:")
        col.prop(props, "image_size", text="")
        col = row.column(align=True)
        col.label(text="Num:")
        col.prop(props, "num_images", text="")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Name:")
        row.prop(props, "auto_image_name", text="Auto")
        r = col.row(align=True)
        r.prop(props, "image_name", text="")
        r.enabled = not props.auto_image_name


class OPENAI_PT_ImageToolEditImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Edit Image"
    bl_parent_id = "OPENAI_PT_ImageTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='GREASEPENCIL')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_edit_image_props

        layout.prop(sc, "openai_image_tool_edit_image_base_image", text="Base")
        layout.prop(sc, "openai_image_tool_edit_image_mask_image", text="Mask")

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        ops = row.operator(
            image.OPENAI_OT_EditImage.bl_idname, icon='PLAY', text="")
        ops.prompt = props.prompt
        ops.num_images = props.num_images
        ops.image_size = props.image_size
        base_image = sc.openai_image_tool_edit_image_base_image
        if base_image is not None:
            ops.base_image_name = base_image.name
        mask_image = sc.openai_image_tool_edit_image_mask_image
        if mask_image is not None:
            ops.mask_image_name = mask_image.name

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Size:")
        col.prop(props, "image_size", text="")
        col = row.column(align=True)
        col.label(text="Num:")
        col.prop(props, "num_images", text="")


class OPENAI_PT_ImageToolGenereateVariationImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generate Variation Image"
    bl_parent_id = "OPENAI_PT_ImageTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='DUPLICATE')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_generate_variation_image_props

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(sc, "openai_image_tool_generate_variation_image_base_image",
                 text="")
        ops = row.operator(image.OPENAI_OT_GenerateVariationImage.bl_idname,
                           icon='PLAY', text="")
        ops.num_images = props.num_images
        ops.image_size = props.image_size
        base_image = sc.openai_image_tool_generate_variation_image_base_image
        if base_image is not None:
            ops.base_image_name = base_image.name

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Size:")
        col.prop(props, "image_size", text="")
        col = row.column(align=True)
        col.label(text="Num:")
        col.prop(props, "num_images", text="")


class OPENAI_PT_ImageToolGeneratedImages(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generated Images"
    bl_parent_id = "OPENAI_PT_ImageTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='IMAGE_DATA')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_generate_image_props

        row = layout.row(align=True)
        row.template_icon_view(props, "edit_target", show_labels=True)
        col = row.column(align=True)
        op = col.operator(image.OPENAI_OT_LoadImage.bl_idname, text="",
                          icon='IMAGE_DATA')
        op.image_filepath = props.edit_target
        op = col.operator(image.OPENAI_OT_RemoveImage.bl_idname, text="",
                          icon='TRASH')
        op.image_filepath = props.edit_target


class OPENAI_PT_AudioToolSequenceEditor(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Audio Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout
        icon_collection = sc.openai_icon_collection["openai_base"]

        layout.label(text="", icon_value=icon_collection.icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_AudioToolTranscribeSoundStrip(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Transcribe Sound Strip"
    bl_parent_id = "OPENAI_PT_AudioToolSequenceEditor"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='SOUND')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_audio_tool_transcribe_sound_strip_props

        layout.prop(props, "selected_sound_strip")

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        col = row.column(align=True)
        col.prop(props, "transcribe_target", text="")
        col.enabled = not props.selected_sound_strip
        ops = row.operator(audio.OPENAI_OT_TranscribeSoundStrip.bl_idname,
                           icon='PLAY', text="")
        ops.prompt = props.prompt
        ops.temperature = props.temperature
        ops.language = props.language
        ops.target = 'TEXT_STRIP'
        if props.selected_sound_strip:
            strip = context.scene.sequence_editor.active_strip
            if strip is not None:
                ops.source_sound_strip_name = strip.name
        else:
            ops.source_sound_strip_name = props.transcribe_target
        if props.auto_sequence_channel:
            strip = context.scene.sequence_editor.active_strip
            if strip is not None:
                ops.target_sequence_channel = strip.channel
        else:
            ops.target_sequence_channel = props.sequence_channel

        layout.separator()

        layout.prop(props, "prompt")

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Language:")
        col.prop(props, "language", text="")
        col = row.column(align=True)
        col.label(text="Temperature:")
        col.prop(props, "temperature", text="")

        layout.separator()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Result:")
        row.prop(props, "auto_sequence_channel", text="Auto")
        r = col.row(align=True)
        r.prop(props, "sequence_channel", text="Channel")
        r.enabled = not props.auto_sequence_channel


class OPENAI_PT_AudioToolTextEditor(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Audio Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout
        icon_collection = sc.openai_icon_collection["openai_base"]

        layout.label(text="", icon_value=icon_collection.icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_AudioToolTranscribeAudioFile(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Transcribe Audio"
    bl_parent_id = "OPENAI_PT_AudioToolTextEditor"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='SOUND')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_audio_tool_transcribe_audio_file_props

        layout.prop(props, "source", expand=True)

        layout.separator()

        row = layout.row(align=True)
        if props.source == 'AUDIO_FILE':
            row.operator(audio.OPENAI_OT_OpenAudioFile.bl_idname, text="",
                         icon='FILEBROWSER')
            row.prop(props, "source_audio_filepath", text="")
        elif props.source == 'SOUND_DATA_BLOCK':
            row = layout.row(align=True)
            row.prop(sc, "openai_audio_tool_source_sound_data_block", text="")
        col = row.column(align=True)
        col.operator_context = 'EXEC_DEFAULT'
        op = col.operator(audio.OPENAI_OT_TranscribeAudioFile.bl_idname,
                          text="", icon='PLAY')
        op.prompt = props.prompt
        op.temperature = props.temperature
        op.language = props.language
        if props.source == 'AUDIO_FILE':
            op.audio_filepath = props.source_audio_filepath
        elif props.source == 'SOUND_DATA_BLOCK':
            sound_data_block = sc.openai_audio_tool_source_sound_data_block
            if sound_data_block is not None:
                op.audio_filepath = sound_data_block.filepath
        if props.current_text:
            if context.space_data.text is not None:
                op.target_text_name = context.space_data.text.name
            else:
                op.target_text_name = "Untitled"
        else:
            if sc.openai_audio_tool_target_text is not None:
                op.target_text_name = sc.openai_audio_tool_target_text.name

        layout.separator()

        layout.prop(props, "prompt")

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Language:")
        col.prop(props, "language", text="")
        col = row.column(align=True)
        col.label(text="Temperature:")
        col.prop(props, "temperature", text="")

        layout.separator()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Result:")
        row.prop(props, "current_text", text="Current Text")
        r = col.row(align=True)
        r.prop(sc, "openai_audio_tool_target_text", text="")
        r.enabled = not props.current_text


class OPENAI_PT_ChatTool(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Chat Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout
        icon_collection = sc.openai_icon_collection["openai_base"]

        layout.label(text="", icon_value=icon_collection.icon_id)

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_chat_tool_props

        row = layout.row()
        row.alignment = 'LEFT'
        row.label(text="Topic:")
        row.prop(props, "new_topic")
        row = row.row(align=True)
        row.enabled = not props.new_topic
        op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="",
                          icon='DUPLICATE')
        if props.topic:
            op.topic = props.topic
        op.part = -1
        op.role = 'ALL'
        op.target = 'CLIPBOARD'
        op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="",
                          icon='TEXT')
        if props.topic:
            op.topic = props.topic
        op.part = -1
        op.role = 'ALL'
        op.target = 'TEXT'

        if props.new_topic:
            layout.prop(props, "new_topic_name", text="")
        else:
            row = layout.row(align=True)
            row.prop(props, "topic", text="")
            op = row.operator(chat.OPENAI_OT_RemoveChat.bl_idname, text="",
                              icon='TRASH')
            if props.topic:
                op.topic = props.topic


class OPENAI_PT_ChatToolPrompt(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Prompt"
    bl_parent_id = "OPENAI_PT_ChatTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='CONSOLE')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_chat_tool_props

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        op = row.operator(chat.OPENAI_OT_Chat.bl_idname, icon='PLAY', text="")
        op.prompt = props.prompt
        if props.topic:
            op.topic = props.topic
        op.new_topic = props.new_topic
        op.new_topic_name = props.new_topic_name
        op.num_conditions = len(sc.openai_chat_tool_conditions)
        for i, condition in enumerate(sc.openai_chat_tool_conditions):
            item = op.conditions.add()
            item.condition = condition.condition

        row = layout.row()
        row.alignment = 'LEFT'
        row.label(text="Conditions:")
        row.operator(chat.OPENAI_OT_AddChatCondition.bl_idname, text="",
                     icon="PLUS")
        for i, condition in enumerate(sc.openai_chat_tool_conditions):
            row = layout.row()
            row.prop(condition, "condition", text=f"{i}")
            op = row.operator(chat.OPENAI_OT_RemoveChatCondition.bl_idname,
                              text="", icon="CANCEL")
            op.index_to_remove = i


class OPENAI_PT_ChatToolLog(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Log"
    bl_parent_id = "OPENAI_PT_ChatTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='WORDWRAP_ON')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_chat_tool_props

        if props.new_topic or not props.topic:
            return

        chat_file = ChatTextFile()
        chat_file.load_from_topic(props.topic)

        for part in range(chat_file.num_parts()):
            user_data = chat_file.get_user_data(part)
            condition_data = chat_file.get_condition_data(part)
            response_data = chat_file.get_response_data(part)

            # Draw header.
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.label(text=f"[{part+1}]    ")
            op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="",
                              icon='DUPLICATE')
            op.topic = props.topic
            op.part = part
            op.role = 'ALL'
            op.target = 'CLIPBOARD'
            op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="",
                              icon='TEXT')
            op.topic = props.topic
            op.part = part
            op.role = 'ALL'
            op.target = 'TEXT'

            # Draw user data.
            lines = user_data.split("\n")
            row = layout.row()
            row.label(text="", icon='USER')
            col = row.column()
            draw_data_on_ui_layout(context, col, lines)

            # Draw condition data.
            if len(condition_data) != 0:
                row = layout.row()
                row.label(text="", icon='MODIFIER')
                col = row.column()
                draw_data_on_ui_layout(context, col, condition_data)

            layout.separator()

            # Draw response data.
            sections = parse_response_data(response_data)
            row = layout.row()
            row.label(text="", icon='LIGHT')
            col = row.column()
            code_index = 0
            for section in sections:
                lines = section["body"].split("\n")
                if section["kind"] == 'TEXT':
                    c = col.column()
                    draw_data_on_ui_layout(context, c, lines)
                elif section["kind"] == 'CODE':
                    r = col.row(align=True)
                    c = r.box().column(align=True)
                    draw_data_on_ui_layout(context, c, lines)
                    c = r.column(align=True)
                    op = c.operator(chat.OPENAI_OT_RunChatCode.bl_idname,
                                    icon='PLAY', text="")
                    op.topic = props.topic
                    op.part = part
                    op.code_index = code_index
                    op = c.operator(chat.OPENAI_OT_CopyChatCode.bl_idname,
                                    icon='DUPLICATE', text="")
                    op.topic = props.topic
                    op.part = part
                    op.code_index = code_index
                    op.target = 'CLIPBOARD'
                    op = c.operator(chat.OPENAI_OT_CopyChatCode.bl_idname,
                                    icon='TEXT', text="")
                    op.topic = props.topic
                    op.part = part
                    op.code_index = code_index
                    op.target = 'TEXT'

                    error_key = error_storage.get_error_key(
                        'CHAT', props.topic, part, code_index)
                    error_message = error_storage.get_error(error_key)
                    if error_message:
                        r = col.row(align=True)
                        c = r.column(align=True)
                        c.alert = True
                        draw_data_on_ui_layout(context, c, [error_message])
                        c = r.column(align=True)
                        op = c.operator(
                            chat.OPENAI_OT_CopyChatCodeError.bl_idname,
                            icon='DUPLICATE', text="")
                        op.topic = props.topic
                        op.part = part
                        op.code_index = code_index

                    code_index += 1

            layout.separator(factor=2.0)


class OPENAI_PT_CodeTool(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Code Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout
        icon_collection = sc.openai_icon_collection["openai_base"]

        layout.label(text="", icon_value=icon_collection.icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_CodeToolPrompt(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Prompt"
    bl_parent_id = "OPENAI_PT_CodeTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='CONSOLE')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_code_tool_props

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        op = row.operator(code.OPENAI_OT_GenerateCode.bl_idname, icon='PLAY',
                          text="")
        op.prompt = props.prompt
        op.execute_immediately = True
        op.show_text_editor = False
        op.num_conditions = len(sc.openai_code_tool_conditions)
        for i, condition in enumerate(sc.openai_code_tool_conditions):
            item = op.conditions.add()
            item.condition = condition.condition
        op = row.operator(code.OPENAI_OT_GenerateCodeFromAudio.bl_idname,
                          icon='REC', text="")
        op.num_conditions = len(sc.openai_code_tool_conditions)
        for i, condition in enumerate(sc.openai_code_tool_conditions):
            item = op.conditions.add()
            item.condition = condition.condition

        row = layout.row()
        row.alignment = 'LEFT'
        row.label(text="Conditions:")
        op = row.operator(code.OPENAI_OT_AddCodeCondition.bl_idname, text="",
                          icon="PLUS")
        op.target = 'CODE_TOOL'
        for i, condition in enumerate(sc.openai_code_tool_conditions):
            row = layout.row()
            row.prop(condition, "condition", text=f"{i}")
            op = row.operator(code.OPENAI_OT_RemoveCodeCondition.bl_idname,
                              text="", icon="CANCEL")
            op.index_to_remove = i
            op.target = 'CODE_TOOL'


class OPENAI_PT_CodeToolGeneratedCode(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Generated Code"
    bl_parent_id = "OPENAI_PT_CodeTool"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='WORDWRAP_ON')

    def draw(self, context):
        layout = self.layout

        code_files = glob.glob(f"{CODE_DATA_DIR}/**/*.py", recursive=True)
        for file in code_files:
            code_name = os.path.splitext(os.path.basename(file))[0]
            error_key = error_storage.get_error_key('CODE', code_name, 0, 0)
            error_message = error_storage.get_error(error_key)
            row = layout.row(align=True)
            op = row.operator(code.OPENAI_OT_RunCode.bl_idname, text=code_name)
            op.code = code_name
            op = row.operator(code.OPENAI_OT_CopyCode.bl_idname, text="",
                              icon='DUPLICATE')
            op.code = code_name
            op.target = 'CLIPBOARD'
            op = row.operator(code.OPENAI_OT_CopyCode.bl_idname, text="",
                              icon='TEXT')
            op.code = code_name
            op.target = 'TEXT'
            op = row.operator(code.OPENAI_OT_RemoveCode.bl_idname, text="",
                              icon='TRASH')
            op.code = code_name
            if error_message:
                r = layout.row(align=True)
                c = r.column(align=True)
                c.alert = True
                draw_data_on_ui_layout(context, c, [error_message])
                c = r.column(align=True)
                op = c.operator(code.OPENAI_OT_CopyCodeError.bl_idname,
                                icon='DUPLICATE', text="")
                op.code = code_name


class OPENAI_PT_CodeToolTextEditor(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Code Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout
        icon_collection = sc.openai_icon_collection["openai_base"]

        layout.label(text="", icon_value=icon_collection.icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_CodeToolGenerateCode(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generate Code"
    bl_parent_id = "OPENAI_PT_CodeToolTextEditor"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='CONSOLE')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_code_tool_generate_code_props
        conditions = sc.openai_code_tool_generate_code_conditions

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        op = row.operator(code.OPENAI_OT_GenerateCode.bl_idname, icon='PLAY',
                          text="")
        op.prompt = props.prompt
        op.execute_immediately = False
        op.show_text_editor = True
        op.num_conditions = len(conditions)
        op.new_code_name = props.prompt[0:64]
        for i, condition in enumerate(conditions):
            item = op.conditions.add()
            item.condition = condition.condition

        row = layout.row()
        row.alignment = 'LEFT'
        row.label(text="Conditions:")
        op = row.operator(code.OPENAI_OT_AddCodeCondition.bl_idname, text="",
                          icon="PLUS")
        op.target = 'GENERATE_CODE'
        for i, condition in enumerate(conditions):
            row = layout.row()
            row.prop(condition, "condition", text=f"{i}")
            op = row.operator(code.OPENAI_OT_RemoveCodeCondition.bl_idname,
                              text="", icon="CANCEL")
            op.index_to_remove = i
            op.target = 'GENERATE_CODE'


class OPENAI_PT_CodeToolEditCode(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Edit Code"
    bl_parent_id = "OPENAI_PT_CodeToolTextEditor"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='GREASEPENCIL')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_code_tool_edit_code_props

        layout.prop(sc, "openai_code_tool_edit_code_edit_target_text_block",
                    text="Edit")

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        op = row.operator(code.OPENAI_OT_EditCode.bl_idname, icon='PLAY',
                          text="")
        op.prompt = props.prompt
        target_text_block = \
            sc.openai_code_tool_edit_code_edit_target_text_block
        if target_text_block is not None:
            op.edit_target_text_block_name = target_text_block.name
        conditions = sc.openai_code_tool_edit_code_conditions
        op.num_conditions = len(conditions)
        for i, condition in enumerate(conditions):
            item = op.conditions.add()
            item.condition = condition.condition

        row = layout.row()
        row.alignment = 'LEFT'
        row.label(text="Conditions:")
        op = row.operator(code.OPENAI_OT_AddCodeCondition.bl_idname, text="",
                          icon="PLUS")
        op.target = 'FIX_CODE'
        conditions = sc.openai_code_tool_edit_code_conditions
        for i, condition in enumerate(conditions):
            row = layout.row()
            row.prop(condition, "condition", text=f"{i}")
            op = row.operator(code.OPENAI_OT_RemoveCodeCondition.bl_idname,
                              text="", icon="CANCEL")
            op.index_to_remove = i
            op.target = 'FIX_CODE'


class OPENAI_PT_CodeToolGeneratedCodeTextEditor(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generated Code"
    bl_parent_id = "OPENAI_PT_CodeToolTextEditor"

    def draw_header(self, _):
        layout = self.layout

        layout.label(text="", icon='WORDWRAP_ON')

    def draw(self, context):
        layout = self.layout

        code_files = glob.glob(f"{CODE_DATA_DIR}/**/*.py", recursive=True)
        for file in code_files:
            code_name = os.path.splitext(os.path.basename(file))[0]
            error_key = error_storage.get_error_key('CODE', code_name, 0, 0)
            error_message = error_storage.get_error(error_key)
            row = layout.row(align=True)
            op = row.operator(code.OPENAI_OT_RunCode.bl_idname, text=code_name)
            op.code = code_name
            op = row.operator(code.OPENAI_OT_CopyCode.bl_idname, text="",
                              icon='DUPLICATE')
            op.code = code_name
            op.target = 'CLIPBOARD'
            op = row.operator(code.OPENAI_OT_CopyCode.bl_idname, text="",
                              icon='TEXT')
            op.code = code_name
            op.target = 'TEXT'
            op = row.operator(code.OPENAI_OT_RemoveCode.bl_idname, text="",
                              icon='TRASH')
            op.code = code_name
            if error_message:
                r = layout.row(align=True)
                c = r.column(align=True)
                c.alert = True
                draw_data_on_ui_layout(context, c, [error_message])
                c = r.column(align=True)
                op = c.operator(code.OPENAI_OT_CopyCodeError.bl_idname,
                                icon='DUPLICATE', text="")
                op.code = code_name
