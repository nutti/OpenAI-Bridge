import bpy
import os
import glob

from ..utils.common import (
    CHAT_DATA_DIR,
    ChatTextFile,
    get_area_region_space,
    get_code_from_response_data,
)
from ..utils.threading import (
    sync_request,
    async_request,
)
from ..utils import error_storage


class OPENAI_OT_AskOperatorUsage(bpy.types.Operator):

    bl_idname = "system.openai_ask_operator_usage"
    bl_description = "Ask the usage of the mouse focussed operator"
    bl_label = "Ask Operator Usage"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if hasattr(context, "button_operator"):
            return True

        return False

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        if not hasattr(context, "button_operator"):
            self.report({'WARNING'}, "Failed to find the operator")
            return {'FINISHED'}

        op = context.button_operator
        sp = op.bl_rna.identifier.split("_")
        py_op_func = f"bpy.ops.{sp[0].lower()}.{sp[2].lower()}()"
        op_desc = op.bl_rna.description
        op_name = op.bl_rna.name

        request = {
            "model": prefs.chat_tool_model,
            "messages": [
                {
                    "role": "user",
                    "content": f"Explain about the operator '{op_name}'"
                },
            ]
        }

        options = {
            "topic": f"Ask Operator '{op_name}'",
            "new_topic": True,
            "hidden_conditions": [
                "This question relates to the Blender",
                "Avoid Python code",
                f"Python API to call operator: {py_op_func}",
                f"Operator description in Blender Application: {op_desc}",
            ]
        }

        if not prefs.async_execution:
            sync_request(api_key, 'CHAT', request, options, context, self)
        else:
            async_request(api_key, 'CHAT', request, options)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}


class OPENAI_OT_AskPropertyUsage(bpy.types.Operator):

    bl_idname = "system.openai_ask_property_usage"
    bl_description = "Ask the usage of the mouse focussed property"
    bl_label = "Ask Property Usage"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "button_prop"):
            return False
        if not hasattr(context, "button_pointer"):
            return False

        return True

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        if not hasattr(context, "button_pointer") or not hasattr(context, "button_prop"):
            self.report({'WARNING'}, "Failed to find the pointer or property")
            return {'CANCELLED'}

        ptr = context.button_pointer
        prop = context.button_prop

        class_name = ptr.bl_rna.name
        class_desc = ptr.bl_rna.description
        py_class = f"bpy.types.{ptr.bl_rna.identifier}"
        prop_name = prop.name
        prop_desc = prop.description
        py_prop_name = prop.identifier

        request = {
            "model": prefs.chat_tool_model,
            "messages": [
                {
                    "role": "user",
                    "content": f"Explain about the property '{prop_name}' of class '{class_name}'"
                },
            ]
        }

        options = {
            "topic": f"Ask Property '{prop_name}' of '{class_name}'",
            "new_topic": True,
            "hidden_conditions": [
                "This question relates to the Blender",
                "Avoid Python code",
                f"Class description in Blender Application: {class_desc}",
                f"Python API for class: {py_class}",
                f"Property description in Blender Application: {prop_desc}",
                f"Python API for property: {py_prop_name}",
            ]
        }

        if not prefs.async_execution:
            sync_request(api_key, 'CHAT', request, options, context, self)
        else:
            async_request(api_key, 'CHAT', request, options)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}


class OPENAI_OT_AddChatCondition(bpy.types.Operator):

    bl_idname = "system.openai_add_chat_condition"
    bl_description = "Add chat condition"
    bl_label = "Add Chat Condition"
    bl_options = {'REGISTER'}

    def execute(self, context):
        sc = context.scene

        sc.openai_chat_tool_conditions.add()

        return {'FINISHED'}


class OPENAI_OT_RemoveChatCondition(bpy.types.Operator):

    bl_idname = "system.openai_remove_chat_condition"
    bl_description = "Remove chat condition"
    bl_label = "Remove Chat Condition"
    bl_options = {'REGISTER'}

    index_to_remove: bpy.props.IntProperty(
        name="Index to Remove",
        default=0,
        min=0,
    )

    def execute(self, context):
        sc = context.scene

        sc.openai_chat_tool_conditions.remove(self.index_to_remove)

        return {'FINISHED'}


class OPENAI_OT_CopyChatLog(bpy.types.Operator):

    bl_idname = "system.openai_copy_chat_log"
    bl_description = "Copy chat log"
    bl_label = "Copy Chat Log"
    bl_options = {'REGISTER'}

    topic: bpy.props.StringProperty(
        name="Topic",
    )
    part: bpy.props.IntProperty(
        name="Part",
        description="Part of topic to be copied. -1 is all",
        default=-1,
        min=-1,
    )
    role: bpy.props.EnumProperty(
        name="Role",
        items=[
            ('USER', "User", "User"),
            ('CONDITION', "Condition", "Condition"),
            ('RESPONSE', "Response", "Response"),
            ('ALL', "All", "All"),
        ],
        default='ALL',
    )
    target: bpy.props.EnumProperty(
        name="Target",
        description="Paste target",
        items=[
            ('CLIPBOARD', "Clipboard", "Clipboard"),
            ('TEXT', "Text", "Text"),
        ],
        default='CLIPBOARD'
    )

    def create_text_to_copy_for_part(self, part, chat_file):
        text_to_copy = ""
        if self.role == 'USER':
            text_to_copy += chat_file.get_user_data(part)
        elif self.role == 'CONDITION':
            text_to_copy += "\n".join(chat_file.get_condition_data(part))
        elif self.role == 'RESPONSE':
            text_to_copy += chat_file.get_response_data(part)
        elif self.role == 'ALL':
            text_to_copy += chat_file.get_user_data(part)
            text_to_copy += "\n".join(chat_file.get_condition_data(part))
            text_to_copy += chat_file.get_response_data(part)

        return text_to_copy

    def execute(self, context):
        chat_file = ChatTextFile()
        chat_file.load_from_topic(self.topic)

        text_to_copy = ""
        if self.part == -1:
            for part in range(chat_file.num_parts()):
                text_to_copy += self.create_text_to_copy_for_part(part, chat_file)
        else:
            text_to_copy = self.create_text_to_copy_for_part(self.part, chat_file)

        if self.target == 'CLIPBOARD':
            context.window_manager.clipboard = text_to_copy
        elif self.target == 'TEXT':
            text_data = bpy.data.texts.new(self.topic)
            text_data.clear()
            text_data.write(text_to_copy)
            # Focus on the chat in Text Editor.
            _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
            if space is not None:
                space.text = text_data

        return {'FINISHED'}


class OPENAI_OT_CopyChatCode(bpy.types.Operator):

    bl_idname = "system.openai_copy_chat_code"
    bl_description = "Copy chat code"
    bl_label = "Copy Chat Code"
    bl_options = {'REGISTER'}

    topic: bpy.props.StringProperty(
        name="Topic",
    )
    part: bpy.props.IntProperty(
        name="Part",
        description="Part of topic to be copied. -1 is all",
        default=0,
        min=0,
    )
    code_index: bpy.props.IntProperty(
        name="Code Index",
        description="Code index of part to be copied.",
        default=0,
        min=0,
    )
    target: bpy.props.EnumProperty(
        name="Target",
        description="Paste target",
        items=[
            ('CLIPBOARD', "Clipboard", "Clipboard"),
            ('TEXT', "Text", "Text"),
        ],
        default='CLIPBOARD'
    )

    def execute(self, context):
        chat_file = ChatTextFile()
        chat_file.load_from_topic(self.topic)

        response_data = chat_file.get_response_data(self.part)
        code_to_copy = get_code_from_response_data(response_data, self.code_index)
        if code_to_copy is None:
            self.report({'WARNING'}, "Failed to find the target code")
            return {'CANCELLED'}

        if self.target == 'CLIPBOARD':
            context.window_manager.clipboard = code_to_copy
        elif self.target == 'TEXT':
            text_data = bpy.data.texts.new(f"{self.topic}-{self.part}-{self.code_index}")
            text_data.clear()
            text_data.write(code_to_copy)
            # Focus on the chat in Text Editor.
            _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
            if space is not None:
                space.text = text_data

        return {'FINISHED'}


class OPENAI_OT_RunChatCode(bpy.types.Operator):

    bl_idname = "system.openai_run_chat_code"
    bl_description = "Run chat code"
    bl_label = "Run Chat Code"
    bl_options = {'REGISTER'}

    topic: bpy.props.StringProperty(
        name="Topic",
    )
    part: bpy.props.IntProperty(
        name="Part",
        description="Part of topic to be copied. -1 is all",
        default=0,
        min=0,
    )
    code_index: bpy.props.IntProperty(
        name="Code Index",
        description="Code index of part to be copied.",
        default=0,
        min=0,
    )

    def execute(self, context):
        chat_file = ChatTextFile()
        chat_file.load_from_topic(self.topic)

        response_data = chat_file.get_response_data(self.part)
        code_to_execute = get_code_from_response_data(response_data, self.code_index)
        if code_to_execute is None:
            self.report({'WARNING'}, "Failed to find the target code")
            return {'CANCELLED'}

        error_key = error_storage.get_error_key('CHAT', self.topic, self.part, self.code_index)
        try:
            exec(code_to_execute)
        except Exception as e:
            error_message = f"Error: {e}"
            error_storage.store_error(error_key, error_message)
            return {'CANCELLED'}

        error_storage.clear_error(error_key)

        return {'FINISHED'}


class OPENAI_OT_RemoveChat(bpy.types.Operator):

    bl_idname = "system.openai_remove_chat"
    bl_description = "Remove chat"
    bl_label = "Remove Chat"
    bl_options = {'REGISTER'}

    topic: bpy.props.StringProperty(
        name="Code",
    )

    def execute(self, context):
        ChatTextFile.remove(self.topic)

        return {'FINISHED'}


class OPENAI_OT_CopyChatCodeError(bpy.types.Operator):

    bl_idname = "system.openai_copy_chat_code_error"
    bl_description = "Copy chat code error"
    bl_label = "Copy Chat Code Error"
    bl_options = {'REGISTER'}

    topic: bpy.props.StringProperty(
        name="Topic",
    )
    part: bpy.props.IntProperty(
        name="Part",
        description="Part of topic to be copied. -1 is all",
        default=0,
        min=0,
    )
    code_index: bpy.props.IntProperty(
        name="Code Index",
        description="Code index of part to be copied.",
        default=0,
        min=0,
    )

    def execute(self, context):
        error_key = error_storage.get_error_key('CHAT', self.topic, self.part, self.code_index)

        error_message = error_storage.get_error(error_key)
        if error_message is None:
            self.report({'WARNING'}, f"Failed to get error message (Error Key: {error_key})")
            return {'CANCELLED'}

        context.window_manager.clipboard = error_message

        return {'FINISHED'}


class OPENAI_ChatOperatorConditionProperties(bpy.types.PropertyGroup):
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
        type=OPENAI_ChatOperatorConditionProperties,
    )

    new_topic: bpy.props.BoolProperty(
        name="New Topic",
        default=True,
    )

    new_topic_name: bpy.props.StringProperty(
        name="New Topic Name",
        default="Blender Chat"
    )

    def get_topics(self, context):
        topic_dir = f"{CHAT_DATA_DIR}/topics"
        if not os.path.isdir(topic_dir):
            return []

        items = []
        topic_files = glob.glob(f"{topic_dir}/**/*.json", recursive=True)
        for file in topic_files:
            topic_name = os.path.splitext(os.path.basename(file))[0]
            items.append((topic_name, topic_name, file))
        return items

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

        layout.separator()

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
            "model": prefs.chat_tool_model,
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
            "hidden_conditions": [
                "The question is for the Blender",
            ]
        }
        if self.new_topic:
            options["topic"] = self.new_topic_name
        else:
            options["topic"] = self.topic

        if not prefs.async_execution:
            sync_request(api_key, 'CHAT', request, options, context, self)
        else:
            async_request(api_key, 'CHAT', request, options)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
