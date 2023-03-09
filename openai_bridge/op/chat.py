import bpy

from ..utils.threading import (
    RequestHandler,
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
        RequestHandler.add_request(api_key, 'CHAT', request, options)

        # Run Message Processing Timer if it has not launched yet.
        bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
