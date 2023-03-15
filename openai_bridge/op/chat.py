import bpy
import glob
import os
from ..utils.common import CHAT_DATA_DIR

from ..utils.threading import (
    async_request,
)


class OPENAI_ConditionPropertyCollection(bpy.types.PropertyGroup):
    condition: bpy.props.StringProperty(
        name="Condition",
    )


class OPENAI_OT_Chat(bpy.types.Operator):

    bl_idname = "system.openai_chat"
    bl_description = "Chat via OpenAI API"
    bl_label = "Chat"
    bl_options = {'REGISTER'}

    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    num_conditions: bpy.props.IntProperty(
        name="Number of Conditions",
        default=1,
        min=0,
        max=10,
    )
    conditions: bpy.props.CollectionProperty(
        name="Conditions",
        type=OPENAI_ConditionPropertyCollection,
    )

    def get_topics(self, context):
        chat_dir = f"{CHAT_DATA_DIR}/topics"
        if not os.path.isdir(chat_dir):
            return []

        items = []
        topic_files = glob.glob(f"{chat_dir}/**/*.txt", recursive=True)
        for file in topic_files:
            topic_name = os.path.splitext(os.path.basename(file))[0]
            items.append((topic_name, topic_name, file))
        return items

    new_topic: bpy.props.BoolProperty(
        name="New Topic",
        default=True,
    )

    new_topic_name: bpy.props.StringProperty(
        name="New Topic Name",
        default="Blender Chat"
    )

    topic: bpy.props.EnumProperty(
        name="Topic",
        items=get_topics,
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "new_topic")
        if self.new_topic:
            layout.prop(self, "new_topic_name")
        else:
            layout.prop(self, "topic")

        layout.prop(self, "prompt")
        layout.label(text="Conditions:")
        for i, condition in enumerate(self.conditions):
            row = layout.row()
            sp = row.split(factor=0.03)
            sp.label(text="")
            sp = sp.split(factor=1.0)
            sp.prop(condition, "condition", text=f"{i+1}")

    def invoke(self, context, event):
        wm = context.window_manager
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        self.conditions.clear()

        for i in range(self.num_conditions):
            self.conditions.add()

        return wm.invoke_props_dialog(self, width=prefs.popup_menu_width)

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": self.prompt
                },
            ]
        }
        for condition in self.conditions:
            if condition.condition != "":
                request["messages"].append(
                    {
                        "role": "system",
                        "content": condition.condition
                    }
                )

        options = {
            "new_topic": self.new_topic,
        }
        if self.new_topic:
            options["topic"] = self.new_topic_name
        else:
            options["topic"] = self.topic

        async_request(api_key, 'CHAT', request, options)

        # Run Message Processing Timer if it has not launched yet.
        bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
