import os

import bpy
from bpy_extras.io_utils import ImportHelper

from ..utils.threading import (
    async_request,
)


class OPENAI_OT_TranscriptAudio(bpy.types.Operator, ImportHelper):

    bl_idname = "system.openai_transcript_audio"
    bl_description = "Transcript audio via OpenAI API"
    bl_label = "Transcript Audio"
    bl_options = {'REGISTER'}

    filename_ext = ".mp3,.wav"

    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        items=[
            ('en', "English", "English"),       # TODO: Add more languages
        ],
        default='en',
    )
    display_target: bpy.props.EnumProperty(
        name="Display Target",
        items=[
            ('TEXT_OBJECT', "Text Object", "Text Object"),
            ('TEXT_EDITOR', "Text Editor", "Text Editor"),
        ],
    )

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.prop(self, "prompt")

        layout.separator()

        layout.prop(self, "display_target")
        if self.display_target == 'TEXT_EDITOR':
            layout.prop(sc, "openai_audio_target_text", text="Text")
        elif self.display_target == 'TEXT_OBJECT':
            layout.prop(sc, "openai_audio_target_text_object", text="Object")

        layout.separator()

        layout.prop(self, "temperature")
        layout.prop(self, "language")

    def invoke(self, context, event):
        wm = context.window_manager

        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        sc = context.scene
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        request = {
            "file": (os.path.basename(self.properties.filepath), open(self.properties.filepath, "rb")),
            "model": (None, "whisper-1"),
            "prompt": (None, self.prompt),
            "response_format": (None, "json"),
            "temperature": (None, f"{self.temperature}"),
            "language": (None, self.language),
        }
        options = {
            "display_target": self.display_target,
            "target_text_name": sc.openai_audio_target_text.name if sc.openai_audio_target_text else None,
            "target_text_object_name": sc.openai_audio_target_text_object.name if sc.openai_audio_target_text_object else None,
        }

        async_request(api_key, 'AUDIO', request, options)

        # Run Message Processing Timer if it has not launched yet.
        bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
