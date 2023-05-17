if "bpy" in locals():
    import importlib
    # pylint: disable=E0601
    importlib.reload(menu)
    importlib.reload(panel)
    importlib.reload(tool)
else:
    from . import menu
    from . import panel
    from . import tool

# pylint: disable=C0413
import bpy


def register_tools():
    bpy.utils.register_tool(tool.OPENAI_WST_ImageTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_AudioTool, separator=True)
    bpy.utils.register_tool(tool.OPENAI_WST_ChatTool, separator=True,
                            group=True)
    bpy.utils.register_tool(tool.OPENAI_WST_CodeTool,
                            after={tool.OPENAI_WST_ChatTool.bl_idname})


def unregister_tools():
    bpy.utils.unregister_tool(tool.OPENAI_WST_CodeTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_ChatTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_AudioTool)
    bpy.utils.unregister_tool(tool.OPENAI_WST_ImageTool)
