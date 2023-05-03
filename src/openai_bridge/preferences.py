import bpy
from .utils import pip
from .utils.audio_recorder import support_audio_recording
from .utils.common import (
    draw_data_on_ui_layout,
    check_api_connection,
    api_connection_enabled,
)
from .utils.addon_updater import AddonUpdatorManager


class OPENAI_OT_CheckAddonUpdate(bpy.types.Operator):
    bl_idname = "system.openai_check_addon_update"
    bl_label = "Check Update"
    bl_description = "Check Add-on Update"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, _):
        updater = AddonUpdatorManager.get_instance()
        updater.check_update_candidate()

        return {'FINISHED'}


class OPENAI_OT_UpdateAddon(bpy.types.Operator):
    bl_idname = "system.openai_update_addon"
    bl_label = "Update"
    bl_description = "Update Add-on"
    bl_options = {'REGISTER', 'UNDO'}

    branch_name: bpy.props.StringProperty(
        name="Branch Name",
        description="Branch name to update",
        default="",
    )

    def execute(self, _):
        updater = AddonUpdatorManager.get_instance()
        updater.update(self.branch_name)

        return {'FINISHED'}


def get_update_candidate_branches(_, __):
    updater = AddonUpdatorManager.get_instance()
    if not updater.candidate_checked():
        return []

    return [(name, name, "") for name in updater.get_candidate_branch_names()]


class OPENAI_OT_CheckAPIConnection(bpy.types.Operator):

    bl_idname = "system.openai_check_api_connection"
    bl_description = "Check connection to OpenAI API"
    bl_label = "Check API Connection"
    bl_options = {'REGISTER'}

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        prefs.connection_status = check_api_connection(
            prefs.api_key, prefs.http_proxy, prefs.https_proxy)

        return {'FINISHED'}


class OPENAI_OT_EnableAudioInput(bpy.types.Operator):

    bl_idname = "system.openai_enable_audio_input"
    bl_description = """Enable to input from audio (This install 'pyaudio'
library to Blender Python environment)"""
    bl_label = "Enable Audio Input"
    bl_options = {'REGISTER'}

    def execute(self, _):
        ret_code = pip.install_package("pyaudio")
        if ret_code != 0:
            self.report(
                {'WARNING'},
                "Failed to enable audio input. See details on the console.")
            return {'CANCELLED'}

        bpy.ops.script.reload()

        return {'FINISHED'}


class OPENAI_Preferences(bpy.types.AddonPreferences):
    bl_idname = "openai_bridge"

    category: bpy.props.EnumProperty(
        name="Category",
        description="Configuration Category",
        items=[
            ('SYSTEM', "System", "System configuration"),
            ('UPDATE', "Update", "Add-on Update"),
            ('IMAGE_TOOL', "Image Tool", "Image tool configuration"),
            ('AUDIO_TOOL', "Audio Tool", "Audio tool configuration"),
            ('CHAT_TOOL', "Chat Tool", "Chat tool configuration"),
            ('CODE_TOOL', "Code Tool", "Code tool configuration"),
        ],
        default='SYSTEM',
    )

    api_key: bpy.props.StringProperty(
        name="API Key",
        description="OpenAI API key",
        subtype='PASSWORD',
    )
    http_proxy: bpy.props.StringProperty(
        name="HTTP Proxy",
        description="""Proxy configuration for HTTP
(ex: http://user:password@hostname:port)""",
    )
    https_proxy: bpy.props.StringProperty(
        name="HTTPS Proxy",
        description="""Proxy configuration for HTTPS
(ex: http://user:password@hostname:port)""",
    )
    connection_status: bpy.props.StringProperty(
        name="Connection Status",
        description="Connection status",
    )

    popup_menu_width: bpy.props.IntProperty(
        name="Popup Menu Width",
        description="Width of the popup menu from workspace tools",
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

    updater_branch_to_update: bpy.props.EnumProperty(
        name="branch",
        description="Target branch to update add-on",
        items=get_update_candidate_branches
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
    chat_tool_log_wrap_width: bpy.props.FloatProperty(
        name="Wrap Width",
        description="Wrap width of the chat tool log",
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
        description="Language for the audio input in the code tool",
        items=[
            ('en', "English", "English"),
            ('ja', "Japanese", "Japanese"),
            # TODO: Add more languages
        ],
        default='en',
    )

    code_tool_audio_record_format: bpy.props.EnumProperty(
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
    code_tool_audio_record_channels: bpy.props.IntProperty(
        name="Channels",
        description="Channels for the audio recording",
        default=2,
        min=1,
        max=2,
    )
    code_tool_audio_record_rate: bpy.props.IntProperty(
        name="Rate",
        description="Sampling rate for the audio recording",
        default=44100,
        min=44100,
        max=44100,
    )
    code_tool_audio_record_chunk_size: bpy.props.IntProperty(
        name="Chunk Size",
        description="Frames per buffer",
        default=1024,
        min=512,
        max=4096,
    )
    code_tool_audio_record_silence_threshold: bpy.props.IntProperty(
        name="Silence Threshold",
        description="Threshold to stop the audio recording",
        default=100,
        min=0,
        max=65536,
    )
    code_tool_audio_record_silence_duration_limit: bpy.props.IntProperty(
        name="Silence Duration Limit",
        description="The seconds to stop the audio recording",
        default=2,
        min=0,
        max=10,
    )

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        row = layout.row()
        row.prop(self, "category", expand=True)

        if self.category == 'SYSTEM':
            row = layout.row(align=True)
            row.prop(self, "api_key")
            col = row.column()
            col.alignment = 'CENTER'
            col.operator(OPENAI_OT_CheckAPIConnection.bl_idname)
            sp = layout.split(factor=0.03)
            sp.column()   # for spacer.
            sp = sp.split(factor=1.0).box()
            sp.label(text="[Connection Status]")
            draw_data_on_ui_layout(
                context, sp, [self.connection_status], 0.08,
                alert=not api_connection_enabled(context))
            layout.prop(self, "http_proxy")
            layout.prop(self, "https_proxy")

            row = layout.row()
            op = row.operator(bpy.types.WM_OT_url_open.bl_idname,
                              text="Register OpenAI API", icon='URL')
            op.url = "https://openai.com/blog/openai-api"
            op = row.operator(bpy.types.WM_OT_url_open.bl_idname,
                              text="OpenAI API Pricing", icon='URL')
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
                    row.prop(self, "request_status_location", expand=True,
                             text="Location")

            layout.separator()

            layout.label(text="Usage Statistics:")
            box = layout.box()

            stats_image_tool = sc.openai_usage_statistics_image_tool
            sp = box.split(factor=0.5)
            sub_box = sp.box()
            sub_box.label(text="[Image Tool]")
            col = sub_box.column()
            row = col.row()
            row.label(text="1024x1024")
            row.label(text=f"{stats_image_tool.images_1024x1024} images")
            row = col.row()
            row.label(text="512x512")
            row.label(text=f"{stats_image_tool.images_512x512} images")
            row = col.row()
            row.label(text="256x256")
            row.label(text=f"{stats_image_tool.images_256x256} images")

            stats_audio_tool = sc.openai_usage_statistics_audio_tool
            sub_box = sp.box()
            sub_box.label(text="[Audio Tool]")
            col = sub_box.column()
            row = col.row()
            row.label(text="whiper-1")
            row.label(text=f"{stats_audio_tool.seconds_whisper} seconds")

            stats_chat_tool = sc.openai_usage_statistics_chat_tool
            sp = box.split(factor=0.5)
            sub_box = sp.box()
            sub_box.label(text="[Chat Tool]")
            col = sub_box.column()
            row = col.row()
            row.label(text="gpt-3.5-turbo")
            row.label(text=f"{stats_chat_tool.tokens_gpt35_turbo} tokens")
            row = col.row()
            row.label(text="gpt-4")
            row.label(text=f"{stats_chat_tool.tokens_gpt4_8k} tokens")
            row = col.row()
            row.label(text="gpt-4-32k")
            row.label(text=f"{stats_chat_tool.tokens_gpt4_32k} tokens")

            stats_code_tool = sc.openai_usage_statistics_code_tool
            sp = sp.split(factor=1.0)
            sub_box = sp.box()
            sub_box.label(text="[Code Tool]")
            col = sub_box.column()
            row = col.row()
            row.label(text="gpt-3.5-turbo")
            row.label(text=f"{stats_code_tool.tokens_gpt35_turbo} tokens")
            row = col.row()
            row.label(text="gpt-4")
            row.label(text=f"{stats_code_tool.tokens_gpt4_8k} tokens")
            row = col.row()
            row.label(text="gpt-4-32k")
            row.label(text=f"{stats_code_tool.tokens_gpt4_32k} tokens")

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
            row.prop(self, "chat_tool_log_wrap_width")
        elif self.category == 'CODE_TOOL':
            col = layout.column()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(self, "code_tool_model")

            layout.separator()

            if support_audio_recording():
                layout.label(text="Audio Input Configuration:")

                sp_outer = layout.split(factor=0.05)
                sp_outer.column()   # for spacer.
                sp_outer = sp_outer.split(factor=0.5)
                col = sp_outer.column()
                col.alignment = 'LEFT'
                col.prop(self, "code_tool_audio_language", text="Language")

                layout.label(text="Recording Configuration:")

                sp_outer = layout.split(factor=0.05)
                sp_outer.column()   # for spacer.
                sp_outer = sp_outer.split(factor=0.5)
                col = sp_outer.column()
                col.prop(self, "code_tool_audio_record_format")
                col.prop(self, "code_tool_audio_record_channels")
                col.prop(self, "code_tool_audio_record_rate")
                col.prop(self, "code_tool_audio_record_chunk_size")
                col.prop(self, "code_tool_audio_record_silence_threshold")
                col.prop(self, "code_tool_audio_record_silence_duration_limit")
            else:
                sp = layout.split(factor=0.5)
                col = sp.column()
                col.operator(OPENAI_OT_EnableAudioInput.bl_idname)

        elif self.category == 'UPDATE':
            updater = AddonUpdatorManager.get_instance()

            layout.separator()

            if not updater.candidate_checked():
                col = layout.column()
                col.scale_y = 2
                row = col.row()
                row.operator(OPENAI_OT_CheckAddonUpdate.bl_idname,
                             text="Check 'OpenAI Bridge' add-on update",
                             icon='FILE_REFRESH')
            else:
                row = layout.row(align=True)
                row.scale_y = 2
                col = row.column()
                col.operator(OPENAI_OT_CheckAddonUpdate.bl_idname,
                             text="Check 'OpenAI Bridge' add-on update",
                             icon='FILE_REFRESH')
                col = row.column()
                if updater.latest_version() != "":
                    col.enabled = True
                    ops = col.operator(
                        OPENAI_OT_UpdateAddon.bl_idname,
                        text="""Update to the latest release version
(version: {})""".format(updater.latest_version()),
                        icon='TRIA_DOWN_BAR')
                    ops.branch_name = updater.latest_version()
                else:
                    col.enabled = False
                    col.operator(OPENAI_OT_UpdateAddon.bl_idname,
                                 text="No updates are available.")

                layout.separator()
                layout.label(text="Manual Update:")
                row = layout.row(align=True)
                row.prop(self, "updater_branch_to_update", text="Target")
                ops = row.operator(
                    OPENAI_OT_UpdateAddon.bl_idname, text="Update",
                    icon='TRIA_DOWN_BAR')
                ops.branch_name = self.updater_branch_to_update

                layout.separator()
                if updater.has_error():
                    box = layout.box()
                    box.label(text=updater.error(), icon='CANCEL')
                elif updater.has_info():
                    box = layout.box()
                    box.label(text=updater.info(), icon='ERROR')
