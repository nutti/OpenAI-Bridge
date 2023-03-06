import bpy


class OPENAI_Preferences(bpy.types.AddonPreferences):
    bl_idname = "openai_bridge"

    api_key: bpy.props.StringProperty(
        name="API Key",
    )

    def draw(self, _):
        layout = self.layout
        layout.prop(self, "api_key")
