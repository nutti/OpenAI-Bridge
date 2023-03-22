import bpy

from ..utils.threading import (
    sync_request,
    async_request,
)


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
    image_name: bpy.props.StringProperty(
        name="Image Name",
        description="Name of image data block"
    )
    remove_file: bpy.props.BoolProperty(
        name="Remove File",
        description="If true, remove generated files after the image block is loaded",
        default=False,
    )

    sync: bpy.props.BoolProperty(
        name="Sync",
        description="Synchronous execution if true",
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "prompt")
        layout.prop(self, "image_name")

        layout.separator()

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
            "remove_file": self.remove_file,
            "image_name": self.image_name,
        }

        if self.sync:
            sync_request(api_key, 'IMAGE', request, options, context, self)
        else:
            async_request(api_key, 'IMAGE', request, options)
            # Run Message Processing Timer if it has not launched yet.
            bpy.ops.system.openai_process_message()

        print(f"Sent Request: f{request}")
        return {'FINISHED'}
