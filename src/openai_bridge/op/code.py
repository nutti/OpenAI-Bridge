import bpy
import glob
import os
from ..utils.common import CODE_DATA_DIR

from ..utils.threading import (
    sync_request,
    async_request,
)


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

    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    use_latest_error_message: bpy.props.BoolProperty(
        name="Use Latest Error Message",
        default=True,
    )
    error_message: bpy.props.StringProperty(
        name="Error Message",
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

        layout.prop(self, "mode")
        if self.mode == 'GENERATE':
            layout.prop(self, "new_code_name")
        else:
            layout.prop(self, "code")

        layout.separator()

        if self.mode == 'GENERATE':
            layout.prop(self, "prompt")
        elif self.mode == 'FIX':
            layout.prop(self, "error_message")

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
            options["code"] = self.new_code_name
        else:
            options["use_latest_error_message"] = self.use_latest_error_message
            options["error_message"] = self.error_message
            options["code"] = self.code

        if self.sync:
            sync_request(api_key, 'CODE', request, options, context, self)
        else:
            async_request(api_key, 'CODE', request, options)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
