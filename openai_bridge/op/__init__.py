if "bpy" in locals():
    import importlib
    importlib.reload(chat)
    importlib.reload(image)
else:
    from . import chat
    from . import image

import bpy


classes = [
    chat.OPENAI_OT_Chat,
    image.OPENAI_OT_GeneateImage,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
