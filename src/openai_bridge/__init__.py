bl_info = {
    "name": "OpenAI Bridge",
    "author": "nutti",
    "version": (1, 0, 0),
    "blender": (3, 5, 0),
    "location": "3D View",
    "warning": "",
    "description": "Bridge between Blender and OpenAI",
    "doc_url": "",
    "tracker_url": "",
    "category": "System",
}


if "bpy" in locals():
    import importlib
    # pylint: disable=E0601
    importlib.reload(utils)
    utils.bl_class_registry.BlClassRegistry.cleanup()
    importlib.reload(op)
    importlib.reload(properties)
    importlib.reload(preferences)
    importlib.reload(ui)
else:
    import bpy
    from . import op
    from . import properties
    from . import preferences
    from . import ui
    from . import utils

# pylint: disable=C0413
import os
import bpy


def register_updater(info):
    config = utils.addon_updater.AddonUpdaterConfig()
    config.owner = "nutti"
    config.repository = "OpenAI-Bridge"
    config.current_addon_path = os.path.dirname(os.path.realpath(__file__))
    config.branches = ["main"]
    ridx = config.current_addon_path.rfind(utils.addon_updater.get_separator())
    config.addon_directory = config.current_addon_path[:ridx]
    config.min_release_version = info["version"]
    config.default_target_addon_path = "openai_bridge"
    config.target_addon_path = {
        "main": "src{}openai_bridge".format(
            utils.addon_updater.get_separator()),
    }
    updater = utils.addon_updater.AddonUpdaterManager.get_instance()
    updater.init(config)


def menu_func(self, context):
    sc = context.scene
    layout = self.layout
    icon_collection = sc.openai_icon_collection["openai_base"]

    layout.separator()
    layout.operator(op.chat.OPENAI_OT_Ask.bl_idname,
                    icon_value=icon_collection.icon_id)
    layout.operator(op.code.OPENAI_OT_GenerateCodeExample.bl_idname,
                    icon_value=icon_collection.icon_id)


def register():
    register_updater(bl_info)

    properties.register_properties()

    utils.bl_class_registry.BlClassRegistry.register()
    ui.register_tools()
    utils.threading.RequestHandler.start()

    bpy.types.WM_MT_button_context.append(menu_func)

    user_prefs = bpy.context.preferences
    prefs = user_prefs.addons["openai_bridge"].preferences

    prefs.connection_status = utils.common.check_api_connection(
        prefs.api_key, prefs.http_proxy, prefs.https_proxy)


def unregister():
    bpy.types.WM_MT_button_context.remove(menu_func)

    utils.threading.RequestHandler.stop()

    ui.unregister_tools()
    utils.bl_class_registry.BlClassRegistry.unregister()
    properties.unregister_properties()
