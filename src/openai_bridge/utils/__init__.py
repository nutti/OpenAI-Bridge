if "bpy" in locals():
    import importlib
    importlib.reload(common)
    importlib.reload(threading)
else:
    from . import common
    from . import threading

import bpy


def register():
    threading.RequestHandler.start()


def unregister():
    threading.RequestHandler.stop()
