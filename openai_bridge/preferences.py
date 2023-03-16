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

    def draw(self, _):
        layout = self.layout

        layout.prop(self, "api_key")

        sp = layout.split(factor=0.35)
        sp.prop(self, "popup_menu_width")
