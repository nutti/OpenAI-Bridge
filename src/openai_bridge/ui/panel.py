import bpy

from ..op import image
from ..op import audio


class OPENAI_PT_GenerateImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generate Image"

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


class OPENAI_PT_EditImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Edit Image"

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


class OPENAI_PT_TranscribeSoundStrip(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Transcribe Sound Strip"

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


class OPENAI_PT_TranscribeAudio(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'TEXT_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Transcribe Audio"

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
