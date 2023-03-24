import bpy


class OPENAI_Preferences(bpy.types.AddonPreferences):
    bl_idname = "openai_bridge"

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

        layout.prop(self, "api_key")

        layout.separator()

        sp = layout.split(factor=0.35)
        sp.prop(self, "popup_menu_width")
        sp.prop(self, "async_execution")

        layout.separator()

        layout.prop(self, "audio_tool_model")
        layout.prop(self, "chat_tool_model")
        layout.prop(self, "code_tool_model")
