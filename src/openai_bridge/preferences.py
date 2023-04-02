import bpy


class OPENAI_Preferences(bpy.types.AddonPreferences):
    bl_idname = "openai_bridge"

    category: bpy.props.EnumProperty(
        name="Category",
        items=[
            ('SYSTEM', "System", "System configuration"),
            ('IMAGE_TOOL', "Image Tool", "Image tool configuration"),
            ('AUDIO_TOOL', "Audio Tool", "Audio tool configuration"),
            ('CHAT_TOOL', "Chat Tool", "Chat tool configuration"),
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

    def draw(self, _):
        layout = self.layout

        row = layout.row()
        row.prop(self, "category", expand=True)

        if self.category == 'SYSTEM':
            layout.prop(self, "api_key")

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
