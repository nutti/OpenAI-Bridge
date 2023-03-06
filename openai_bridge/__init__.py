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
    importlib.reload(preferences)
    importlib.reload(ui)
    importlib.reload(utils)
else:
    import bpy
    from . import op
    from . import preferences
    from . import ui
    from . import utils


def register():
    op.register()
    bpy.utils.register_class(preferences.OPENAI_Preferences)
    ui.register()

    bpy.utils.register_class(utils.threading.OPENAI_OT_ProcessMessage)
    bpy.utils.register_class(utils.threading.OPENAI_OT_Error)
    utils.threading.RequestHandler.start()


def unregister():
    bpy.utils.unregister_class(utils.threading.OPENAI_OT_ProcessMessage)
    bpy.utils.unregister_class(utils.threading.OPENAI_OT_Error)
    utils.threading.RequestHandler.stop()

    ui.unregister()
    bpy.utils.unregister_class(preferences.OPENAI_Preferences)
    op.unregister()
