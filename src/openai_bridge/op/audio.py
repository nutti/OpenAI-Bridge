import os

import bpy
from bpy_extras.io_utils import ImportHelper

from ..utils.threading import (
    sync_request,
    async_request,
)
from ..utils.common import api_connection_enabled
from ..utils.bl_class_registry import BlClassRegistry


@BlClassRegistry()
class OPENAI_OT_TranscribeSoundStrip(bpy.types.Operator):

    bl_idname = "system.openai_transcribe_sound_strip"
    bl_description = "Transcribe the sound strip via OpenAI API"
    bl_label = "Transcribe Sound Strip"
    bl_options = {'REGISTER'}

    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Optional text to specify the style",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        description="""Higher value makes the output more random.
Lower value makes the output more deterministic.""",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        description="Language of the input audio",
        items=[
            ('en', "English", "English"),
            ('ja', "Japanese", "Japanese"),
            # TODO: Add more languages
        ],
        default='en',
    )
    target: bpy.props.EnumProperty(
        name="Target",
        items=[
            ('TEXT_EDITOR', "Text Editor", "Text Editor"),
            ('TEXT_STRIP', "Text Strip", "Text Strip"),
        ],
    )
    sound_strip_name: bpy.props.StringProperty(
        name="Sound Strip Name",
        description="Name of the sound strip to transcribe",
    )
    sequence_channel: bpy.props.IntProperty(
        name="Target Sequence Channel",
        description="""Sequence channel where the transcription result to be
created""",
        min=1,
        max=128,
        default=1,
    )

    @classmethod
    def poll(cls, context):
        if not api_connection_enabled(context):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_audio_tool_transcribe_sound_strip_props

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

    def invoke(self, context, _):
        wm = context.window_manager
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        if context.scene.sequence_editor.active_strip is None:
            return {'CANCELLED'}
        if context.scene.sequence_editor.active_strip.type != 'SOUND':
            return {'CANCELLED'}

        self.sound_strip_name = context.scene.sequence_editor.active_strip.name
        self.target = 'TEXT_STRIP'

        return wm.invoke_props_dialog(self, width=prefs.popup_menu_width)

    def execute(self, context):
        sc = context.scene
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        sequences = context.scene.sequence_editor.sequences
        sequence = sequences[self.sound_strip_name]
        filepath = sequence.sound.filepath

        request = {
            "file": (filepath, open(filepath, "rb")),   # pylint: disable=R1732
            "model": (None, prefs.audio_tool_model),
            "prompt": (None, self.prompt),
            "response_format": (None, "json"),
            "temperature": (None, f"{self.temperature}"),
            "language": (None, self.language),
        }

        strip_end = sequence.frame_final_start + sequence.frame_final_duration
        options = {
            "target": self.target,
            "target_sequence_channel": self.sequence_channel,
            "strip_start": sequence.frame_final_start,
            "strip_end": strip_end,
            "fps": sc.render.fps / sc.render.fps_base,
            "http_proxy": prefs.http_proxy,
            "https_proxy": prefs.https_proxy,
        }

        if not prefs.async_execution:
            sync_request(api_key, 'TRANSCRIBE_AUDIO', request, options,
                         context, self)
        else:
            transaction_data = {
                "type": 'AUDIO',
                "title": filepath[0:32],
            }
            async_request(api_key, 'TRANSCRIBE_AUDIO', request, options,
                          transaction_data)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}


@BlClassRegistry()
class OPENAI_OT_OpenAudioFile(bpy.types.Operator, ImportHelper):

    bl_idname = "system.openai_open_audio_file"
    bl_description = "Open an audio file"
    bl_label = "Open Audio File"
    bl_options = {'REGISTER'}

    filename_ext = ".mp3,.wav"

    def execute(self, context):
        sc = context.scene
        props = sc.openai_audio_tool_transcribe_audio_file_props

        props.source_audio_filepath = self.properties.filepath

        context.area.tag_redraw()

        return {'FINISHED'}


@BlClassRegistry()
class OPENAI_OT_TranscribeAudioFile(bpy.types.Operator):

    bl_idname = "system.openai_transcribe_audio_file"
    bl_description = "Transcribe the audio via OpenAI API"
    bl_label = "Transcribe Audio"
    bl_options = {'REGISTER'}

    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Optional text to specify the style",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        description="""Higher value makes the output more random.
Lower value makes the output more deterministic.""",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        description="Language of the input audio",
        items=[
            ('en', "English", "English"),
            ('ja', "Japanese", "Japanese"),
            # TODO: Add more languages
        ],
        default='en',
    )
    audio_filepath: bpy.props.StringProperty(
        name="Audio Filepath",
        description="Filepath of the audio file to transcribe",
    )
    target_text_block_name: bpy.props.StringProperty(
        name="Target Text Block Name",
        description="""Name of target text block to where the transcript is
saved""",
    )

    @classmethod
    def poll(cls, context):
        if not api_connection_enabled(context):
            return False
        return True

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        request = {
            "file": (os.path.basename(self.audio_filepath),
                     open(self.audio_filepath, "rb")),  # pylint: disable=R1732
            "model": (None, prefs.audio_tool_model),
            "prompt": (None, self.prompt),
            "response_format": (None, "json"),
            "temperature": (None, f"{self.temperature}"),
            "language": (None, self.language),
        }

        options = {
            "target": 'TEXT_EDITOR',
            "target_text_name": self.target_text_block_name,
            "http_proxy": prefs.http_proxy,
            "https_proxy": prefs.https_proxy,
        }

        if not prefs.async_execution:
            sync_request(
                api_key, 'TRANSCRIBE_AUDIO', request, options, context, self)
        else:
            transaction_data = {
                "type": 'AUDIO',
                "title": self.audio_filepath[0:32],
            }
            async_request(
                api_key, 'TRANSCRIBE_AUDIO', request, options,
                transaction_data)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
