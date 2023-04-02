import bpy
import glob
import os
from ..utils.common import (
    CODE_DATA_DIR,
    get_area_region_space,
)

from ..utils.threading import (
    sync_request,
    async_request,
)
from ..utils import error_storage


class OPENAI_OT_AddCodeCondition(bpy.types.Operator):

    bl_idname = "system.openai_add_code_condition"
    bl_description = "Add code condition"
    bl_label = "Add Coe Condition"
    bl_options = {'REGISTER'}

    def execute(self, context):
        sc = context.scene

        sc.openai_code_tool_conditions.add()

        return {'FINISHED'}


class OPENAI_OT_RemoveCodeCondition(bpy.types.Operator):

    bl_idname = "system.openai_remove_code_condition"
    bl_description = "Remove code condition"
    bl_label = "Remove Code Condition"
    bl_options = {'REGISTER'}

    index_to_remove: bpy.props.IntProperty(
        name="Index to Remove",
        default=0,
        min=0,
    )

    def execute(self, context):
        sc = context.scene

        sc.openai_code_tool_conditions.remove(self.index_to_remove)

        return {'FINISHED'}


class OPENAI_OT_RunCode(bpy.types.Operator):

    bl_idname = "system.openai_run_code"
    bl_description = "Run code"
    bl_label = "Run Code"
    bl_options = {'REGISTER'}

    code: bpy.props.StringProperty(
        name="Code",
    )

    def execute(self, context):
        print(self.code)
        error_key = error_storage.get_error_key('CODE', self.code, 0, 0)

        try:
            filepath = f"{CODE_DATA_DIR}/{self.code}.py"
            with open(filepath, "r", encoding="utf-8") as f:
                code_to_execute = f.read()
            exec(code_to_execute)
        except Exception as e:
            error_message = f"Error: {e}"
            error_storage.store_error(error_key, error_message)
            return {'CANCELLED'}

        error_storage.clear_error(error_key)

        return {'FINISHED'}


class OPENAI_OT_CopyCode(bpy.types.Operator):

    bl_idname = "system.openai_copy_code"
    bl_description = "Copy code"
    bl_label = "Copy Code"
    bl_options = {'REGISTER'}

    code: bpy.props.StringProperty(
        name="Code",
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
        filepath = f"{CODE_DATA_DIR}/{self.code}.py"
        with open(filepath, "r", encoding="utf-8") as f:
            code_to_copy = f.read()

        if self.target == 'CLIPBOARD':
            context.window_manager.clipboard = code_to_copy
        elif self.target == 'TEXT':
            text_data = bpy.data.texts.new(f"{self.code}.py")
            text_data.clear()
            text_data.write(code_to_copy)
            # Focus on the chat in Text Editor.
            _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
            if space is not None:
                space.text = text_data

        return {'FINISHED'}


class OPENAI_OT_RemoveCode(bpy.types.Operator):

    bl_idname = "system.openai_remove_code"
    bl_description = "Remove code"
    bl_label = "Remove Code"
    bl_options = {'REGISTER'}

    code: bpy.props.StringProperty(
        name="Code",
    )

    def execute(self, context):
        filepath = f"{CODE_DATA_DIR}/{self.code}.py"

        os.remove(filepath)

        return {'FINISHED'}


class OPENAI_OT_CopyCodeError(bpy.types.Operator):

    bl_idname = "system.openai_copy_code_error"
    bl_description = "Copy code error"
    bl_label = "Copy Code Error"
    bl_options = {'REGISTER'}

    code: bpy.props.StringProperty(
        name="Code",
    )

    def execute(self, context):
        error_key = error_storage.get_error_key('CODE', self.code, 0, 0)

        error_message = error_storage.get_error(error_key)
        if error_message is None:
            self.report({'WARNING'}, f"Failed to get error message (Error Key: {error_key})")
            return {'CANCELLED'}

        context.window_manager.clipboard = error_message

        return {'FINISHED'}


class OPENAI_CodeConditionPropertyCollection(bpy.types.PropertyGroup):
    condition: bpy.props.StringProperty(
        name="Condition",
    )


class OPENAI_OT_Code(bpy.types.Operator):

    bl_idname = "system.openai_code"
    bl_description = "Generate code via OpenAI API"
    bl_label = "Code"
    bl_options = {'REGISTER'}

    input_method: bpy.props.EnumProperty(
        name="Input",
        items=[
            ('TEXT', "Text", "Input from text"),
            ('AUDIO', "Audio", "Input from audio"),
        ],
        default='TEXT',
    )

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
        type=OPENAI_CodeConditionPropertyCollection,
    )

    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('GENERATE', "Generate", "Generate the code from the prompt"),
            ('FIX', "Fix", "Fix the code from the error message"),
        ],
        default='GENERATE',
    )

    execute_immediately: bpy.props.BoolProperty(
        name="Execute Immediately",
        description="Execute a generated code immediately",
        default=False,
    )

    def get_codes(self, context):
        code_dir = f"{CODE_DATA_DIR}/codes"
        if not os.path.isdir(code_dir):
            return []

        items = []
        code_files = glob.glob(f"{code_dir}/**/*.txt", recursive=True)
        for file in code_files:
            code_name = os.path.splitext(os.path.basename(file))[0]
            items.append((code_name, code_name, file))
        return items

    new_code_name: bpy.props.StringProperty(
        name="New Code Name",
        default="Blender Code"
    )
    code: bpy.props.EnumProperty(
        name="Code",
        items=get_codes,
    )

    sync: bpy.props.BoolProperty(
        name="Sync",
        description="Synchronous execution if true",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        if self.mode == 'GENERATE':
            layout.prop(self, "prompt")

        layout.separator()

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
            "model": prefs.code_tool_model,
            "messages": []
        }

        if self.mode == 'GENERATE':
            request["messages"].append({
                "role": "user",
                "content": self.prompt
            })
        elif self.mode == 'FIX':
            request["messages"].append({
                "role": "user",
                "content": f"""
This code raise the error. Fix and generate the code again.

Error: {self.error_message}"""
            })

        for condition in self.conditions:
            if condition.condition != "":
                request["messages"].append(
                    {
                        "role": "system",
                        "content": condition.condition
                    }
                )

        conditions_for_bpy_code = [
            "Programming Language: Python",
            "Use Blender Python API",
            "Prefer to use bpy.ops",
            "Prefer small code",
        ]
        for condition in conditions_for_bpy_code:
            request["messages"].extend([
                {
                    "role": "system",
                    "content": condition
                }
            ])

        options = {
            "mode": self.mode,
            "execute_immediately": self.execute_immediately,
        }
        if self.mode == 'GENERATE':
            if self.execute_immediately:
                options["code"] = self.prompt[0:64]
            else:
                options["code"] = self.new_code_name
        else:
            options["code"] = self.code

        if self.sync:
            sync_request(api_key, 'CODE', request, options, context, self)
        else:
            transaction_data = {
                "type": 'CODE',
                "title": options["code"][0:32],
            }
            async_request(api_key, 'CODE', request, options, transaction_data)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
