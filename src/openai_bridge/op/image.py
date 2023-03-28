import bpy
import os

from ..utils.threading import (
    sync_request,
    async_request,
)
from ..utils.common import (
    get_area_region_space,
)


class OPENAI_OT_LoadImage(bpy.types.Operator):

    bl_idname = "system.openai_load_image"
    bl_description = "Load image to the texture data block"
    bl_label = "Load Image"
    bl_options = {'REGISTER', 'UNDO'}

    image_filepath : bpy.props.StringProperty(
        name="Image Filepath",
    )

    def execute(self, context):
        # TODO: Add the option not to open the image with same filepath.
        image = bpy.data.images.load(filepath=self.image_filepath)

        # Focus on the generated image in Image Editor.
        _, _, space = get_area_region_space(context, 'IMAGE_EDITOR', 'WINDOW', 'IMAGE_EDITOR')
        if space is not None:
            space.image = image

        return {'FINISHED'}


class OPENAI_OT_RemoveImage(bpy.types.Operator):

    bl_idname = "system.openai_remove_image"
    bl_description = "Remove image"
    bl_label = "Remove Image"
    bl_options = {'REGISTER', 'UNDO'}

    image_filepath : bpy.props.StringProperty(
        name="Image Filepath",
    )

    def execute(self, context):
        os.remove(self.image_filepath)

        # TODO: Add the option to remove image data block.

        return {'FINISHED'}


class OPENAI_OT_GeneateImage(bpy.types.Operator):

    bl_idname = "system.openai_generate_image"
    bl_description = "Generate image via OpenAI API"
    bl_label = "Generate Image"
    bl_options = {'REGISTER'}

    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    num_images: bpy.props.IntProperty(
        name="Number of Images",
        description="How many images to generate",
        default=1,
        min=1,
        max=10,
    )
    image_size: bpy.props.EnumProperty(
        name="Image Size",
        description="The size of the images to generate",
        items=[
            ('256x256', "256x256", "256x256"),
            ('512x512', "512x512", "512x512"),
            ('1024x1024', "1024x1024", "1024x1024"),
        ]
    )
    auto_image_name: bpy.props.BoolProperty(
        name="Auto Image Name",
        description="Create image name automatically if true",
        default=True,
    )
    image_name: bpy.props.StringProperty(
        name="Image Name",
        description="Name of image data block"
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "prompt")

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Size:")
        col.prop(self, "image_size", text="")
        col = row.column(align=True)
        col.label(text="Num")
        col.prop(self, "num_images", text="")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Name:")
        row.prop(self, "auto_image_name", text="Auto")
        r = col.row(align=True)
        r.prop(self, "image_name", text="")
        r.enabled = not self.auto_image_name

    def invoke(self, context, event):
        wm = context.window_manager
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        return wm.invoke_props_dialog(self, width=prefs.popup_menu_width)

    def execute(self, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences
        api_key = prefs.api_key

        request = {
            "prompt": self.prompt,
            "n": self.num_images,
            "size": self.image_size,
            "response_format": "url",
        }
        options = {
            "image_name": self.image_name,
        }

        if not prefs.async_execution:
            sync_request(api_key, 'IMAGE', request, options, context, self)
        else:
            async_request(api_key, 'IMAGE', request, options)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
