import bpy
import textwrap

from ..op import image
from ..op import audio
from ..op import chat
from ..utils.common import (
    ChatTextFile,
    parse_response_data,
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

        layout.label(text="", icon_value=sc.openai_icon_collection["openai_base"].icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_GenerateImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generate Image"
    bl_parent_id = "OPENAI_PT_ImageTool"

    def draw_header(self, context):
        layout = self.layout

        layout.label(text="", icon='CONSOLE')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_props

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        ops = row.operator(image.OPENAI_OT_GeneateImage.bl_idname, icon='PLAY', text="")
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


class OPENAI_PT_GeneratedImages(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generated Images"
    bl_parent_id = "OPENAI_PT_ImageTool"

    def draw_header(self, context):
        layout = self.layout

        layout.label(text="", icon='IMAGE_DATA')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_props

        row = layout.row(align=True)
        row.template_icon_view(props, "edit_target", show_labels=True)
        col = row.column(align=True)
        op = col.operator(image.OPENAI_OT_LoadImage.bl_idname, text="", icon='IMAGE_DATA')
        op.image_filepath = props.edit_target
        op = col.operator(image.OPENAI_OT_RemoveImage.bl_idname, text="", icon='TRASH')
        op.image_filepath = props.edit_target

        # TODO: Add editing tool


class OPENAI_PT_AudioToolSequenceEditor(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Audio Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout

        layout.label(text="", icon_value=sc.openai_icon_collection["openai_base"].icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_TranscribeSoundStrip(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Transcribe Sound Strip"
    bl_parent_id = "OPENAI_PT_AudioToolSequenceEditor"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout

        layout.label(text="", icon='SOUND')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_audio_tool_props

        layout.prop(props, "selected_sound_strip")

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        col = row.column(align=True)
        col.prop(props, "transcribe_target", text="")
        col.enabled = not props.selected_sound_strip
        ops = row.operator(audio.OPENAI_OT_TranscribeSoundStrip.bl_idname, icon='PLAY', text="")
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
        row.prop(props, "auto_sequence_channel", text="Same Channel")
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

        layout.label(text="", icon_value=sc.openai_icon_collection["openai_base"].icon_id)

    def draw(self, context):
        pass


class OPENAI_PT_TranscribeAudio(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Transcribe Audio"
    bl_parent_id = "OPENAI_PT_AudioToolTextEditor"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout

        layout.label(text="", icon='SOUND')

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_audio_tool_audio_props

        layout.prop(props, "source", expand=True)

        layout.separator()

        row = layout.row(align=True)
        if props.source == 'AUDIO_FILE':
            row.operator(audio.OPENAI_OT_OpenAudioFile.bl_idname, text="", icon='FILEBROWSER')
            row.prop(props, "source_audio_filepath", text="")
        elif props.source == 'SOUND_DATA_BLOCK':
            row = layout.row(align=True)
            row.prop(sc, "openai_audio_tool_source_sound_data_block", text="")
        col = row.column(align=True)
        col.operator_context = 'EXEC_DEFAULT'
        op = col.operator(audio.OPENAI_OT_TranscribeAudio.bl_idname, text="", icon='PLAY')
        op.prompt = props.prompt
        op.temperature = props.temperature
        op.language = props.language
        if props.source == 'AUDIO_FILE':
            op.audio_filepath = props.source_audio_filepath
        elif props.source == 'SOUND_DATA_BLOCK':
            op.audio_filepath = sc.openai_audio_tool_source_sound_data_block.filepath
        if props.current_text:
            op.target_text_name = context.space_data.text.name
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
        r.prop(sc, "openai_audio_tool_target_text", text="Channel")
        r.enabled = not props.current_text


class OPENAI_PT_ChatTool(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Chat Tool"

    def draw_header(self, context):
        sc = context.scene
        layout = self.layout

        layout.label(text="", icon_value=sc.openai_icon_collection["openai_base"].icon_id)

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
        op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="", icon='DUPLICATE')
        if props.topic:
            op.topic = props.topic
        op.part = -1
        op.role = 'ALL'
        op.target = 'CLIPBOARD'
        op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="", icon='TEXT')
        if props.topic:
            op.topic = props.topic
        op.part = -1
        op.role = 'ALL'
        op.target = 'TEXT'

        if props.new_topic:
            layout.prop(props, "new_topic_name", text="")
        else:
            layout.prop(props, "topic", text="")


class OPENAI_PT_ChatPrompt(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Prompt"
    bl_parent_id = "OPENAI_PT_ChatTool"

    def draw_header(self, context):
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
        row.operator(chat.OPENAI_OT_AddChatCondition.bl_idname, text="", icon="PLUS")
        for i, condition in enumerate(sc.openai_chat_tool_conditions):
            row = layout.row()
            row.prop(condition, "condition", text=f"{i}")
            op = row.operator(chat.OPENAI_OT_RemoveChatCondition.bl_idname, text="", icon="CANCEL")
            op.index_to_remove = i


class OPENAI_PT_ChatLog(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_category = "OpenAI"
    bl_label = "Log"
    bl_parent_id = "OPENAI_PT_ChatTool"

    def draw_header(self, context):
        layout = self.layout

        layout.label(text="", icon='WORDWRAP_ON')

    def draw_data(self, context, layout, lines):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        wrapped_length = int(context.region.width * prefs.chat_log_wrap_width)
        wrapper = textwrap.TextWrapper(width=wrapped_length)
        col = layout.column(align=True)
        for l in lines:
            wrappeed_lines = wrapper.wrap(text=l)
            for wl in wrappeed_lines:
                col.scale_y = 0.8
                col.label(text=wl)
            if len(wrappeed_lines) == 0:
                col.label(text="")

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
            op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="", icon='DUPLICATE')
            op.topic = props.topic
            op.part = part
            op.role = 'ALL'
            op.target= 'CLIPBOARD'
            op = row.operator(chat.OPENAI_OT_CopyChatLog.bl_idname, text="", icon='TEXT')
            op.topic = props.topic
            op.part = part
            op.role = 'ALL'
            op.target= 'TEXT'

            # Draw user data.
            lines = user_data.split("\n")
            row = layout.row()
            row.label(text="", icon='USER')
            col = row.column()
            self.draw_data(context, col, lines)

            # Draw condition data.
            if len(condition_data) != 0:
                row = layout.row()
                row.label(text="", icon='MODIFIER')
                col = row.column()
                self.draw_data(context, col, condition_data)

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
                    self.draw_data(context, c, lines)
                elif section["kind"] == 'CODE':
                    r = col.row(align=True)
                    c = r.box().column(align=True)
                    self.draw_data(context, c, lines)
                    c = r.column(align=True)
                    op = c.operator(chat.OPENAI_OT_RunChatCode.bl_idname, icon='PLAY', text="")
                    op.topic = props.topic
                    op.part = part
                    op.code_index = code_index
                    op = c.operator(chat.OPENAI_OT_CopyChatCode.bl_idname, icon='DUPLICATE', text="")
                    op.topic = props.topic
                    op.part = part
                    op.code_index = code_index
                    op.target = 'CLIPBOARD'
                    op = c.operator(chat.OPENAI_OT_CopyChatCode.bl_idname, icon='TEXT', text="")
                    op.topic = props.topic
                    op.part = part
                    op.code_index = code_index
                    op.target = 'TEXT'

                    error_key = error_storage.get_error_key(props.topic, part, code_index)
                    error_message = error_storage.get_error(error_key)
                    if error_message:
                        r = col.row(align=True)
                        c = r.column(align=True)
                        c.alert = True
                        self.draw_data(context, c, [error_message])
                        c = r.column(align=True)
                        op = c.operator(chat.OPENAI_OT_CopyChatCodeError.bl_idname, icon='DUPLICATE', text="")
                        op.topic = props.topic
                        op.part = part
                        op.code_index = code_index

                    code_index += 1

            layout.separator(factor=2.0)
