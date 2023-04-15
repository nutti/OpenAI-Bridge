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
    bpy.utils.register_class(panel.OPENAI_PT_ImageToolGenerateImage)
    bpy.utils.register_class(panel.OPENAI_PT_ImageToolEditImage)
    bpy.utils.register_class(panel.OPENAI_PT_ImageToolGeneratedImages)
    bpy.utils.register_class(panel.OPENAI_PT_AudioToolSequenceEditor)
    bpy.utils.register_class(panel.OPENAI_PT_AudioToolTranscribeSoundStrip)
    bpy.utils.register_class(panel.OPENAI_PT_AudioToolTextEditor)
    bpy.utils.register_class(panel.OPENAI_PT_AudioToolTranscribeAudioFile)
    bpy.utils.register_class(panel.OPENAI_PT_ChatTool)
    bpy.utils.register_class(panel.OPENAI_PT_ChatToolPrompt)
    bpy.utils.register_class(panel.OPENAI_PT_ChatToolLog)
    bpy.utils.register_class(panel.OPENAI_PT_CodeTool)
    bpy.utils.register_class(panel.OPENAI_PT_CodeToolPrompt)
    bpy.utils.register_class(panel.OPENAI_PT_CodeToolGeneratedCode)
    bpy.utils.register_class(panel.OPENAI_PT_CodeToolTextEditor)
    bpy.utils.register_class(panel.OPENAI_PT_CodeToolGenerateCode)
    bpy.utils.register_class(panel.OPENAI_PT_CodeToolEditCode)
    bpy.utils.register_class(panel.OPENAI_PT_CodeToolGeneratedCodeTextEditor)

    bpy.utils.register_tool(tool.OPENAI_WST_ImageTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_AudioTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_ChatTool, separator=True, group=True)
    bpy.utils.register_tool(tool.OPENAI_WST_CodeTool, after={tool.OPENAI_WST_ChatTool.bl_idname})


def unregister():
    bpy.utils.unregister_tool(tool.OPENAI_WST_CodeTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_ChatTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_AudioTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_ImageTool)

    bpy.utils.unregister_class(panel.OPENAI_PT_CodeToolGeneratedCodeTextEditor)
    bpy.utils.unregister_class(panel.OPENAI_PT_CodeToolEditCode)
    bpy.utils.unregister_class(panel.OPENAI_PT_CodeToolGenerateCode)
    bpy.utils.unregister_class(panel.OPENAI_PT_CodeToolTextEditor)
    bpy.utils.unregister_class(panel.OPENAI_PT_CodeToolGeneratedCode)
    bpy.utils.unregister_class(panel.OPENAI_PT_CodeToolPrompt)
    bpy.utils.unregister_class(panel.OPENAI_PT_CodeTool)
    bpy.utils.unregister_class(panel.OPENAI_PT_ChatToolLog)
    bpy.utils.unregister_class(panel.OPENAI_PT_ChatToolPrompt)
    bpy.utils.unregister_class(panel.OPENAI_PT_ChatTool)
    bpy.utils.unregister_class(panel.OPENAI_PT_AudioToolTranscribeAudioFile)
    bpy.utils.unregister_class(panel.OPENAI_PT_AudioToolTextEditor)
    bpy.utils.unregister_class(panel.OPENAI_PT_AudioToolTranscribeSoundStrip)
    bpy.utils.unregister_class(panel.OPENAI_PT_AudioToolSequenceEditor)
    bpy.utils.unregister_class(panel.OPENAI_PT_ImageToolGeneratedImages)
    bpy.utils.unregister_class(panel.OPENAI_PT_ImageToolEditImage)
    bpy.utils.unregister_class(panel.OPENAI_PT_ImageToolGenerateImage)
    bpy.utils.unregister_class(panel.OPENAI_PT_ImageTool)

    bpy.utils.unregister_class(menu.WM_MT_button_context)
