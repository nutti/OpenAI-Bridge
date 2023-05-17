if "bpy" in locals():
    import importlib
    # pylint: disable=E0601
    importlib.reload(audio)
    importlib.reload(chat)
    importlib.reload(code)
    importlib.reload(image)
else:
    from . import audio
    from . import chat
    from . import code
    from . import image

# pylint: disable=C0413
import bpy
