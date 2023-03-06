import bpy
import uuid

from ..utils.threading import (
    RequestHandler,
    OPENAI_OT_ProcessMessage,
)

class OPENAI_OT_Chat(bpy.types.Operator):

    bl_idname = "system.openai_chat"
    bl_description = "Chat via OpenAI API"
    bl_label = "Chat"
    bl_options = {'REGISTER', 'UNDO'}

    _draw_handler = None

    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    text_name: bpy.props.StringProperty(
        name="Text Name",
        description="Name of the text data block in which the chat log is stored"
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        message_key_for_to = uuid.uuid4()
        message_key_for_from = uuid.uuid4()
        OPENAI_OT_ProcessMessage.message_keys_lock.acquire()
        OPENAI_OT_ProcessMessage.message_keys.add(message_key_for_to)
        OPENAI_OT_ProcessMessage.message_keys.add(message_key_for_from)
        OPENAI_OT_ProcessMessage.message_keys_lock.release()

        request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": self.prompt
                }
            ]
        }
        options = {
            "text_name": self.text_name
        }
        RequestHandler.add_request(api_key, [message_key_for_to, message_key_for_from], 'CHAT', request, options)

        # Run Message Processing Timer if it has not launched yet.
        bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
