import bpy
import glob
import os
from ..utils.common import CHAT_DATA_DIR

from ..utils.threading import (
    async_request,
)


class OPENAI_OT_Chat(bpy.types.Operator):

    bl_idname = "system.openai_chat"
    bl_description = "Chat via OpenAI API"
    bl_label = "Chat"
    bl_options = {'REGISTER', 'UNDO'}

    user_prompt: bpy.props.StringProperty(
        name="User Prompt",
    )
    system_prompt: bpy.props.StringProperty(
        name="System Prompt",
    )
    include_old_prompts: bpy.props.BoolProperty(
        name="Include Old Prompt",
        description="Include old prompts in Text Editor",
        default=False,
    )

    def get_topics(self, context):
        chat_dir = f"{CHAT_DATA_DIR}/topics"
        if not os.path.isdir(chat_dir):
            return []

        items = []
        topic_files = glob.glob(f"{chat_dir}/**/*.txt", recursive=True)
        for file in topic_files:
            items.append((file, file, file))
        return items

    topic: bpy.props.EnumProperty(
        name="Topic",
        items=get_topics,
    )

    text_name: bpy.props.StringProperty(
        name="Text Name",
        description="Name of the text data block in which the chat log is stored",
        default="Chat Result",
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
                    "role": "user",
                    "content": self.user_prompt
                },
            ]
        }
        options = {
            "text_name": self.text_name
        }

        async_request(api_key, 'CHAT', request, options)

        # Run Message Processing Timer if it has not launched yet.
        bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
