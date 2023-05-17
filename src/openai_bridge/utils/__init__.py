if "bpy" in locals():
    import importlib
    # pylint: disable=E0601
    importlib.reload(addon_updater)
    importlib.reload(audio_recorder)
    importlib.reload(bl_class_registry)
    importlib.reload(common)
    importlib.reload(error_storage)
    importlib.reload(pip)
    importlib.reload(threading)
else:
    from . import addon_updater
    from . import audio_recorder
    from . import bl_class_registry
    from . import common
    from . import error_storage
    from . import pip
    from . import threading

# pylint: disable=C0413
import bpy


def register():
    threading.RequestHandler.start()


def unregister():
    threading.RequestHandler.stop()
