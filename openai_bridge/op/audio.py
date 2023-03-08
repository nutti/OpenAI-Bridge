import os

import bpy
from bpy_extras.io_utils import ImportHelper
import uuid

from ..utils.threading import (
    RequestHandler,
    OPENAI_OT_ProcessMessage,
)


class OPENAI_OT_TranscriptAudio(bpy.types.Operator, ImportHelper):

    bl_idname = "system.openai_transcript_audio"
    bl_description = "Transcript audio via OpenAI API"
    bl_label = "Transcript Audio"
    bl_options = {'REGISTER', 'UNDO'}

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
    text_name: bpy.props.StringProperty(
        name="Text Name",
        description="Name of the text data block in which the chat log is stored"
    )

    def invoke(self, context, event):
        wm = context.window_manager

        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        message_key = uuid.uuid4()
        OPENAI_OT_ProcessMessage.message_keys_lock.acquire()
        OPENAI_OT_ProcessMessage.message_keys.add(message_key)
        OPENAI_OT_ProcessMessage.message_keys_lock.release()

        request = {
            "file": (os.path.basename(self.properties.filepath), open(self.properties.filepath, "rb")),
            "model": (None, "whisper-1"),
            "prompt": (None, self.prompt),
            "response_format": (None, "json"),
            "temperature": (None, f"{self.temperature}"),
            "language": (None, self.language),
        }
        options = {
            "text_name": self.text_name,
        }
        RequestHandler.add_request(api_key, [message_key], 'AUDIO', request, options)

        # Run Message Processing Timer if it has not launched yet.
        bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
