if "bpy" in locals():
    import importlib
    importlib.reload(menu)
    importlib.reload(panel)
    importlib.reload(tool)
else:
    from . import menu
    from . import panel
    from . import tool

import bpy


def register():
    bpy.utils.register_class(menu.WM_MT_button_context)

    bpy.utils.register_class(panel.OPENAI_PT_ImageTool)
    bpy.utils.register_class(panel.OPENAI_PT_GenerateImage)
    bpy.utils.register_class(panel.OPENAI_PT_GeneratedImages)
    bpy.utils.register_class(panel.OPENAI_PT_AudioToolSequenceEditor)
    bpy.utils.register_class(panel.OPENAI_PT_TranscribeSoundStrip)
    bpy.utils.register_class(panel.OPENAI_PT_AudioToolTextEditor)
    bpy.utils.register_class(panel.OPENAI_PT_TranscribeAudio)
    bpy.utils.register_class(panel.OPENAI_PT_ChatTool)
    bpy.utils.register_class(panel.OPENAI_PT_ChatPrompt)
    bpy.utils.register_class(panel.OPENAI_PT_ChatLog)

    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIImageTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIAudioTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIChatTool, separator=True)


def unregister():

    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIChatTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIAudioTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIImageTool)

    bpy.utils.unregister_class(panel.OPENAI_PT_ChatLog)
    bpy.utils.unregister_class(panel.OPENAI_PT_ChatPrompt)
    bpy.utils.unregister_class(panel.OPENAI_PT_ChatTool)
    bpy.utils.unregister_class(panel.OPENAI_PT_TranscribeAudio)
    bpy.utils.unregister_class(panel.OPENAI_PT_AudioToolTextEditor)
    bpy.utils.unregister_class(panel.OPENAI_PT_TranscribeSoundStrip)
    bpy.utils.unregister_class(panel.OPENAI_PT_AudioToolSequenceEditor)
    bpy.utils.unregister_class(panel.OPENAI_PT_GeneratedImages)
    bpy.utils.unregister_class(panel.OPENAI_PT_GenerateImage)
    bpy.utils.unregister_class(panel.OPENAI_PT_ImageTool)

    bpy.utils.unregister_class(menu.WM_MT_button_context)
