import bpy
import glob
import os
import uuid
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from ..utils.common import (
    AUDIO_DATA_DIR,
    CODE_DATA_DIR,
    get_area_region_space,
)
from ..utils.audio_recorder import (
    AudioRecorder,
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


class OPENAI_OT_CodeFromAudio(bpy.types.Operator):

    bl_idname = "system.openai_code_from_audio"
    bl_description = "Execute code from audio via OpenAI API"
    bl_label = "Code from Audio"
    bl_options = {'REGISTER'}

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

    _timer = None
    _draw_cb = {"space_data": None, "handler": None}
    _recorder = None

    @classmethod
    def draw_status(cls, context):
        font_id = 0

        center_x = context.region.width / 2
        center_y = context.region.height / 2

        # Draw background.
        original_state = gpu.state.blend_get()
        gpu.state.blend_set('ALPHA')
        rect_width = 400.0
        rect_height = 180.0
        vertex_data = {
            "pos": [
                [center_x - rect_width / 2, center_y - rect_height / 2],
                [center_x - rect_width / 2, center_y + rect_height / 2],
                [center_x + rect_width / 2, center_y + rect_height / 2],
                [center_x + rect_width / 2, center_y - rect_height / 2],
            ]
        }
        index_data = [
            [0, 1, 2],
            [2, 3, 0]
        ]
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', vertex_data, indices=index_data)
        shader.bind()
        shader.uniform_float("color", [0.0, 0.0, 0.0, 0.6])
        batch.draw(shader)
        gpu.state.blend_set(original_state)

        str_to_draw = ""
        if cls._recorder:
            if cls._recorder.get_recording_status() == 'WAIT_RECORDING':
                str_to_draw = "Wait Recording ..."
            elif cls._recorder.get_recording_status() == 'RECORDING':
                str_to_draw = "Recording ..."
            elif cls._recorder.get_recording_status() in ('FINISHED', 'ABORTED', 'TERMINATED'):
                str_to_draw = "Finished"

        blf.color(font_id, 0.8, 0.8, 0.8, 1.0)
        blf.size(font_id, 32)
        size = blf.dimensions(font_id, str_to_draw)
        blf.position(font_id, center_x - size[0] / 2, center_y - size[1] / 2 + 5.0, 0.0)
        blf.draw(font_id, str_to_draw)

    def send_request(self, context, record_filename):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        request = {
            "model": prefs.code_tool_model,
            "messages": []
        }

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
            "audio_file": record_filename,
            "audio_model": prefs.audio_tool_model,
            "audio_language": prefs.code_tool_audio_language,
            "mode": 'GENERATE',
            "execute_immediately": True,
        }

        if not prefs.async_execution:
            sync_request(api_key, 'AUDIO_CODE', request, options, context, self)
        else:
            transaction_data = {
                "type": 'CODE',
                "title": "",
            }
            async_request(api_key, 'AUDIO_CODE', request, options, transaction_data)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}

    def finalize(self, context):
        cls = self.__class__

        cls._recorder = None

        if cls._timer is not None:
            wm = context.window_manager
            wm.event_timer_remove(cls._timer)
            cls._timer = None
        if cls._draw_cb["space_data"] is not None and cls._draw_cb["handler"] is not None:
            cls._draw_cb["space_data"].draw_handler_remove(cls._draw_cb["handler"], 'WINDOW')

    def modal(self, context, event):
        cls = self.__class__

        if event.type == 'ESC':
            cls._recorder.abort_recording()

            self.finalize(context)
            context.area.tag_redraw()

            return {'CANCELLED'}
        elif event.type == 'TIMER':
            if cls._recorder is not None and cls._recorder.record_ended():
                dirname = f"{AUDIO_DATA_DIR}/record"
                os.makedirs(dirname, exist_ok=True)
                record_filename = f"{dirname}/{uuid.uuid4()}.wav"
                cls._recorder.save(record_filename)

                self.finalize(context)
                self.send_request(context, record_filename)
                context.area.tag_redraw()

                return {'FINISHED'}

            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def execute(self, context):
        cls = self.__class__
        wm = context.window_manager
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        cls._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        cls._draw_cb["space_data"] = bpy.types.SpaceView3D
        cls._draw_cb["handler"] = bpy.types.SpaceView3D.draw_handler_add(cls.draw_status, (context, ), 'WINDOW', 'POST_PIXEL')

        cls._recorder = AudioRecorder(prefs.audio_record_format, prefs.audio_record_channels, prefs.audio_record_rate,
                                      prefs.audio_record_chunk_size, prefs.audio_record_silence_threshold,
                                      prefs.audio_record_silence_duration_limit)
        cls._recorder.record(async_execution=True)

        return {'RUNNING_MODAL'}


class OPENAI_OT_Code(bpy.types.Operator):

    bl_idname = "system.openai_code"
    bl_description = "Generate code via OpenAI API"
    bl_label = "Code"
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
