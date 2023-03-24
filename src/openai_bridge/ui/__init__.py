if "bpy" in locals():
    import importlib
    importlib.reload(panel)
    importlib.reload(tool)
else:
    from . import panel
    from . import tool

import bpy


def register():
    bpy.utils.register_class(panel.OPENAI_PT_GenerateImage)
    bpy.utils.register_class(panel.OPENAI_PT_EditImage)
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIImageTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIChatTool, separator=True, group=True)
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAICodeTool, after={tool.OPENAI_WST_OpenAIChatTool.bl_idname})
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIAudioTool, after={tool.OPENAI_WST_OpenAIChatTool.bl_idname})


def unregister():
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAICodeTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIChatTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIAudioTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIImageTool)
    bpy.utils.unregister_class(panel.OPENAI_PT_EditImage)
    bpy.utils.unregister_class(panel.OPENAI_PT_GenerateImage)
