bl_info = {
    "name": "OpenAI Bridge",
    "author": "nutti",
    "version": (0, 1, 0),
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
    importlib.reload(op)
    importlib.reload(properties)
    importlib.reload(preferences)
    importlib.reload(ui)
    importlib.reload(utils)
else:
    import bpy
    from . import op
    from . import properties
    from . import preferences
    from . import ui
    from . import utils


def register():
    op.register()
    bpy.utils.register_class(preferences.OPENAI_Preferences)
    ui.register()

    bpy.utils.register_class(utils.threading.OPENAI_OT_ProcessMessage)
    utils.threading.RequestHandler.start()

    properties.register_properties()


def unregister():
    properties.unregister_properties()

    bpy.utils.unregister_class(utils.threading.OPENAI_OT_ProcessMessage)
    utils.threading.RequestHandler.stop()

    ui.unregister()
    bpy.utils.unregister_class(preferences.OPENAI_Preferences)
    op.unregister()
