import bpy
import bpy.utils.previews
import glob
import os

from .utils.common import (
    IMAGE_DATA_DIR,
)


class OPENAI_ImageToolProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Property"
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

    def get_image_previews_items(self, context):
        sc = context.scene
        collection =sc.openai_image_tool_image_collection

        image_dir = f"{IMAGE_DATA_DIR}"
        if not os.path.isdir(image_dir):
            return []

        items = []
        image_files = glob.glob(f"{image_dir}/**/*.png", recursive=True)
        for i, filepath in enumerate(image_files):
            image_name = os.path.splitext(os.path.basename(filepath))[0]
            if collection.get(filepath) is None:
                thumbnail = collection.load(filepath, filepath, 'IMAGE')
            else:
                thumbnail = collection.get(filepath)
            items.append((filepath, image_name, "", thumbnail.icon_id, i))

        return items

    edit_target: bpy.props.EnumProperty(
        name="Edit Target",
        description="Target image for editing",
        items=get_image_previews_items,
    )


def register_properties():
    scene = bpy.types.Scene

    bpy.utils.register_class(OPENAI_ImageToolProperties)

    scene.openai_audio_target_text_object = bpy.props.PointerProperty(
        name="Target Text Object",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'FONT',
    )
    scene.openai_audio_target_text = bpy.props.PointerProperty(
        name="Target Text",
        type=bpy.types.Text,
    )

    scene.openai_image_tool_props = bpy.props.PointerProperty(
        type=OPENAI_ImageToolProperties
    )
    scene.openai_image_tool_image_collection = bpy.utils.previews.new()


def unregister_properties():
    scene = bpy.types.Scene

    bpy.utils.previews.remove(scene.openai_image_tool_image_collection)
    del scene.openai_image_tool_image_collection

    del scene.openai_image_tool_props
    del scene.openai_audio_target_text
    del scene.openai_audio_target_text_object

    bpy.utils.unregister_class(OPENAI_ImageToolProperties)
