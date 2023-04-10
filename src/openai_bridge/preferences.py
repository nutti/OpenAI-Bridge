import bpy
from .utils import pip


class OPENAI_OT_EnableAudioInput(bpy.types.Operator):

    bl_idname = "system.openai_enable_audio_input"
    bl_description = "Enable to input from audio (This install 'pyaudio' library to Blender Python environment)"
    bl_label = "Enable Audio Input"
    bl_options = {'REGISTER'}

    def execute(self, context):
        ret_code = pip.install_package("pyaudio")
        if ret_code != 0:
            self.report({'WARNING'}, "Failed to enable audio input. See details on the console.")
            return {'CANCELLED'}

        return {'FINISHED'}


class OPENAI_Preferences(bpy.types.AddonPreferences):
    bl_idname = "openai_bridge"

    category: bpy.props.EnumProperty(
        name="Category",
        items=[
            ('SYSTEM', "System", "System configuration"),
            ('IMAGE_TOOL', "Image Tool", "Image tool configuration"),
            ('AUDIO_TOOL', "Audio Tool", "Audio tool configuration"),
            ('CHAT_TOOL', "Chat Tool", "Chat tool configuration"),
            ('CODE_TOOL', "Code Tool", "Code tool configuration"),
        ],
    )

    api_key: bpy.props.StringProperty(
        name="API Key",
        subtype='PASSWORD',
    )
    popup_menu_width: bpy.props.IntProperty(
        name="Popup Menu Width",
        default=300,
        min=100,
        max=1000,
    )
    async_execution: bpy.props.BoolProperty(
        name="Async Execution",
        description="Execute operations asynchronously",
        default=True,
    )
    show_request_status: bpy.props.BoolProperty(
        name="Show Request Status",
        description="Show Request Status",
        default=True,
    )
    request_status_location: bpy.props.IntVectorProperty(
        name="Request Status Location",
        description="Location of the request status",
        size=2,
        default=(30, 30),
    )

    audio_tool_model: bpy.props.EnumProperty(
        name="Audio Tool Model",
        description="Model to be used for Audio Tool",
        items=[
            ("whisper-1", "whisper-1", "whisper-1")
        ],
        default="whisper-1",
    )

    chat_tool_model: bpy.props.EnumProperty(
        name="Chat Tool Model",
        description="Model to be used for Chat Tool",
        items=[
            ("gpt-3.5-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo"),
            ("gpt-4", "gpt-4", "gpt-4"),
            ("gpt-4-32k", "gpt-4-32k", "gpt-4-32k"),
        ],
        default="gpt-3.5-turbo",
    )
    chat_log_wrap_width: bpy.props.FloatProperty(
        name="Wrap Width",
        default=0.11,
        min=0.01,
        max=1.0,
        step=0.01,
    )

    code_tool_model: bpy.props.EnumProperty(
        name="Code Tool Model",
        description="Model to be used for Code Tool",
        items=[
            ("gpt-3.5-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo"),
            ("gpt-4", "gpt-4", "gpt-4"),
            ("gpt-4-32k", "gpt-4-32k", "gpt-4-32k"),
        ],
        default="gpt-3.5-turbo",
    )
    code_tool_audio_language: bpy.props.EnumProperty(
        name="Code Tool Audio Language",
        items=[
            ('en', "English", "English"),
            ('ja', "Japanese", "Japanese"),
            # TODO: Add more languages
        ],
        default='en',
    )

    audio_record_format: bpy.props.EnumProperty(
        name="Format",
        description="Formats for the audio recording",
        items=[
            ('FLOAT32', "Float32", "Floating point (32bit)"),
            ('INT32', "Int32", "Integer (32bit)"),
            ('INT24', "Int24", "Integer (24bit)"),
            ('INT16', "Int16", "Integer (16bit)"),
            ('INT8', "Int8", "Integer (8bit)"),
            ('UINT8', "UInt8", "Unsigned integer (8bit)"),
        ],
        default='INT16',
    )
    audio_record_channels: bpy.props.IntProperty(
        name="Channels",
        description="Channels for the audio recording",
        default=2,
        min=1,
        max=2,
    )
    audio_record_rate: bpy.props.IntProperty(
        name="Rate",
        description="Sampling rate for the audio recording",
        default=44100,
        min=44100,
        max=44100,
    )
    audio_record_chunk_size: bpy.props.IntProperty(
        name="Chunk Size",
        description="Frames per buffer",
        default=1024,
        min=512,
        max=4096,
    )
    audio_record_silence_threshold: bpy.props.IntProperty(
        name="Silence Threshold",
        description="Threshold to stop the audio recording",
        default=100,
        min=0,
        max=65536,
    )
    audio_record_silence_duration_limit: bpy.props.IntProperty(
        name="Silence Duration Limit",
        description="The seconds to stop the audio recording",
        default=2,
        min=0,
        max=10,
    )

    def draw(self, _):
        layout = self.layout

        row = layout.row()
        row.prop(self, "category", expand=True)

        if self.category == 'SYSTEM':
            layout.prop(self, "api_key")

            row = layout.row()
            op = row.operator(bpy.types.WM_OT_url_open.bl_idname, text="Register OpenAI API", icon='URL')
            op.url = "https://openai.com/blog/openai-api"
            op = row.operator(bpy.types.WM_OT_url_open.bl_idname, text="OpenAI API Pricing", icon='URL')
            op.url = "https://openai.com/pricing"

            layout.separator()

            col = layout.column()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "popup_menu_width")
            col.separator()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "async_execution")
            row = col.row()
            if self.async_execution:
                row.prop(self, "show_request_status", text="Show Status")
                if self.show_request_status:
                    row.prop(self, "request_status_location", expand=True, text="Location")
            
            layout.separator()

            sp = layout.split(factor=0.35)
            col = sp.column()
            col.operator(OPENAI_OT_EnableAudioInput.bl_idname)
            col.prop(self, "audio_record_format")
            col.prop(self, "audio_record_channels")
            col.prop(self, "audio_record_rate")
            col.prop(self, "audio_record_chunk_size")
            col.prop(self, "audio_record_silence_threshold")
            col.prop(self, "audio_record_silence_duration_limit")

        elif self.category == 'IMAGE_TOOL':
            layout.label(text="No configuration")
        elif self.category == 'AUDIO_TOOL':
            col = layout.column()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "audio_tool_model")
        elif self.category == 'CHAT_TOOL':
            col = layout.column()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "chat_tool_model")
            col.separator()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "chat_log_wrap_width")
        elif self.category == 'CODE_TOOL':
            col = layout.column()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "code_tool_model")
            col.separator()
            col.label(text="Audio:")
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "code_tool_audio_language", text="Language")
