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
    audio.OPENAI_OT_OpenAudioFile,
    audio.OPENAI_OT_TranscribeAudioFile,
    audio.OPENAI_OT_TranscribeSoundStrip,

    chat.OPENAI_OT_AskOperatorUsage,
    chat.OPENAI_OT_AskPropertyUsage,
    chat.OPENAI_ChatOperatorConditionProperties,
    chat.OPENAI_OT_Chat,
    chat.OPENAI_OT_AddChatCondition,
    chat.OPENAI_OT_RemoveChatCondition,
    chat.OPENAI_OT_CopyChatLog,
    chat.OPENAI_OT_CopyChatCode,
    chat.OPENAI_OT_RunChatCode,
    chat.OPENAI_OT_RemoveChat,
    chat.OPENAI_OT_CopyChatCodeError,

    code.OPENAI_OT_AddCodeCondition,
    code.OPENAI_OT_RemoveCodeCondition,
    code.OPENAI_OT_RunCode,
    code.OPENAI_OT_CopyCode,
    code.OPENAI_OT_RemoveCode,
    code.OPENAI_OT_CopyCodeError,
    code.OPENAI_CodeConditionPropertyCollection,
    code.OPENAI_OT_GenerateCode,
    code.OPENAI_OT_GenerateCodeFromAudio,
    code.OPENAI_OT_EditCode,

    image.OPENAI_OT_GeneateImage,
    image.OPENAI_OT_EditImage,
    image.OPENAI_OT_LoadImage,
    image.OPENAI_OT_RemoveImage,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
