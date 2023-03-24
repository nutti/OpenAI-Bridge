if "bpy" in locals():
    import importlib
    importlib.reload(audio)
    importlib.reload(chat)
    importlib.reload(code)
    importlib.reload(image)
else:
    from . import audio
    from . import chat
    from . import code
    from . import image

import bpy


classes = [
    audio.OPENAI_OT_TranscriptAudio,
    chat.OPENAI_ConditionPropertyCollection,
    chat.OPENAI_OT_Chat,
    code.OPENAI_CodeConditionPropertyCollection,
    code.OPENAI_OT_Code,
    image.OPENAI_OT_GeneateImage,
    image.OPENAI_OT_LoadImage,
    image.OPENAI_OT_RemoveImage,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
