if "bpy" in locals():
    import importlib
    importlib.reload(tool)
else:
    from . import tool

import bpy


def register():
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIImageTool, separator=True, group=True)
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIAudioTool, after={tool.OPENAI_WST_OpenAIImageTool.bl_idname})
    bpy.utils.register_tool(tool.OPENAI_WST_OpenAIChatTool, after={tool.OPENAI_WST_OpenAIImageTool.bl_idname})


def unregister():
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIChatTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIAudioTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_OpenAIImageTool)
