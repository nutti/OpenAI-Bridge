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


class OPENAI_AudioToolProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        items=[
            ('en', "English", "English"),       # TODO: Add more languages
        ],
        default='en',
    )

    selected_sound_strip: bpy.props.BoolProperty(
        name="Selected Sound Strip",
        description="Transcribe the selected sound strip",
        default=True,
    )

    def get_transcribe_target_items(self, context):
        items = []
        for seq in context.sequences:
            if seq.type != 'SOUND':
                continue
            seq_name = seq.name
            items.append((seq_name, seq_name, seq_name))

        return items

    transcribe_target: bpy.props.EnumProperty(
        name="Transcribe Target",
        description="Target sound strip for transcribing",
        items=get_transcribe_target_items,
    )

    auto_sequence_channel: bpy.props.BoolProperty(
        name="Auto Sequence Channel",
        description="Create transcription result on the automatically determined channel on sequence editor",
        default=True,
    )
    sequence_channel: bpy.props.IntProperty(
        name="Sequence Channel",
        description="Sequence channel where the transcription result to be created",
        min=1,
        max=128,
        default=1,
    )


class OPENAI_AudioToolAudioProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        items=[
            ('en', "English", "English"),       # TODO: Add more languages
        ],
        default='en',
    )
    source: bpy.props.EnumProperty(
        name="Source",
        items=[
            ('AUDIO_FILE', "Audio File", "Audio File"),
            ('SOUND_DATA_BLOCK', "Sound Data Block", "Sound Data Block"),
        ],
        default='AUDIO_FILE',
    )
    source_audio_filepath: bpy.props.StringProperty(
        name="Source Audio Filepath",
    )

    def get_sound_data_block(self, context):
        items = []
        for sound in bpy.data.sounds:
            items.append((sound.filepath, sound.name, sound.name))

        return items

    current_text: bpy.props.BoolProperty(
        name="Current Text",
        description="Store the transcript result to the current text",
        default=True,
    )
    source_sound_data_block: bpy.props.EnumProperty(
        name="Source Sound Data Block",
        items=get_sound_data_block,
    )


def register_properties():
    scene = bpy.types.Scene

    bpy.utils.register_class(OPENAI_ImageToolProperties)
    bpy.utils.register_class(OPENAI_AudioToolProperties)
    bpy.utils.register_class(OPENAI_AudioToolAudioProperties)

    scene.openai_audio_tool_target_text = bpy.props.PointerProperty(
        name="Target Text",
        type=bpy.types.Text,
    )
    scene.openai_audio_tool_source_sound_data_block = bpy.props.PointerProperty(
        name="Source Sound Data Block",
        type=bpy.types.Sound,
    )

    scene.openai_image_tool_props = bpy.props.PointerProperty(
        type=OPENAI_ImageToolProperties
    )
    scene.openai_image_tool_image_collection = bpy.utils.previews.new()

    scene.openai_audio_tool_props = bpy.props.PointerProperty(
        type=OPENAI_AudioToolProperties,
    )
    scene.openai_audio_tool_audio_props = bpy.props.PointerProperty(
        type=OPENAI_AudioToolAudioProperties,
    )


def unregister_properties():
    scene = bpy.types.Scene

    bpy.utils.previews.remove(scene.openai_image_tool_image_collection)

    del scene.openai_audio_tool_audio_props
    del scene.openai_audio_tool_props
    del scene.openai_image_tool_image_collection
    del scene.openai_image_tool_props
    del scene.openai_audio_tool_source_sound_data_block
    del scene.openai_audio_tool_target_text

    bpy.utils.unregister_class(OPENAI_AudioToolAudioProperties)
    bpy.utils.unregister_class(OPENAI_AudioToolProperties)
    bpy.utils.unregister_class(OPENAI_ImageToolProperties)
