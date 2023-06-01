import glob
import os
import bpy
import bpy.utils.previews

from .utils.common import (
    IMAGE_DATA_DIR,
    CHAT_DATA_DIR,
    ICON_DIR,
)


class OPENAI_ImageToolGenerateImageProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Property",
        description="Description of the image",
    )
    num_images: bpy.props.IntProperty(
        name="Number of Images",
        description="The number of images to generate",
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
        description="Generate image name automatically if true",
        default=True,
    )
    image_name: bpy.props.StringProperty(
        name="Image Name",
        description="Name for a generated image",
    )


class OPENAI_ImageToolEditImageProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Property",
        description="Description of the image",
    )
    num_images: bpy.props.IntProperty(
        name="Number of Images",
        description="The number of images to generate",
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


class OPENAI_ImageToolGenerateVariationImageProperties(
        bpy.types.PropertyGroup):
    num_images: bpy.props.IntProperty(
        name="Number of Images",
        description="The number of images to generate",
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


class OPENAI_ImageToolGeneratedImagesProperties(bpy.types.PropertyGroup):
    def get_image_previews_items(self, context):
        sc = context.scene
        collection = sc.openai_image_tool_image_collection

        image_dir = f"{IMAGE_DATA_DIR}/generated"
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
        description="Image to edit",
        items=get_image_previews_items,
    )


class OPENAI_AudioToolTranscribeSoundStripProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Optional text to specify the style",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        description="""Higher value makes the output more random.
Lower value makes the output more deterministic.""",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        description="Language of the input audio",
        items=[
            ('en', "English", "English"),
            ('ja', "Japanese", "Japanese"),
            # TODO: Add more languages
        ],
        default='en',
    )

    selected_sound_strip: bpy.props.BoolProperty(
        name="Selected Sound Strip",
        description="Transcribe the selected sound strip if true",
        default=True,
    )

    def get_sound_strip_items(self, context):
        items = []
        for seq in context.sequences:
            if seq.type != 'SOUND':
                continue
            seq_name = seq.name
            items.append((seq_name, seq_name, seq_name))

        return items

    sound_strip: bpy.props.EnumProperty(
        name="Sound Strip",
        description="Sound strip to transcribe",
        items=get_sound_strip_items,
    )

    auto_sequence_channel: bpy.props.BoolProperty(
        name="Auto Sequence Channel",
        description="""Create transcription result on the automatically
determined channel on sequence editor""",
        default=True,
    )
    sequence_channel: bpy.props.IntProperty(
        name="Sequence Channel",
        description="""Sequence channel where the transcription result to be
created""",
        min=1,
        max=128,
        default=1,
    )


class OPENAI_AudioToolTranscribeAudioFileProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Optional text to specify the style",
    )
    temperature: bpy.props.FloatProperty(
        name="Temperature",
        description="""Higher value makes the output more random.
Lower value makes the output more deterministic.""",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    language: bpy.props.EnumProperty(
        name="Language",
        description="Language of the input audio",
        items=[
            ('en', "English", "English"),
            ('ja', "Japanese", "Japanese"),
            # TODO: Add more languages
        ],
        default='en',
    )
    input_type: bpy.props.EnumProperty(
        name="Input Type",
        description="Input type of the audio data",
        items=[
            ('AUDIO_FILE', "Audio File", "Audio File"),
            ('SOUND_DATA_BLOCK', "Sound Data Block", "Sound Data Block"),
        ],
        default='AUDIO_FILE',
    )
    audio_filepath: bpy.props.StringProperty(
        name="Audio Filepath",
        description="Filepath of the audio file to transcribe",
    )

    def get_sound_data_block(self, _):
        items = []
        for sound in bpy.data.sounds:
            items.append((sound.filepath, sound.name, sound.name))

        return items

    current_text: bpy.props.BoolProperty(
        name="Current Text",
        description="Store the transcript result to the current text if true",
        default=True,
    )
    sound_data_block: bpy.props.EnumProperty(
        name="Sound Data Block",
        description="Sound data block to transcribe",
        items=get_sound_data_block,
    )


class OPENAI_ChatToolProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Prompt",
    )
    new_topic: bpy.props.BoolProperty(
        name="New Topic",
        description="Create a new topic if true",
        default=True,
    )
    new_topic_name: bpy.props.StringProperty(
        name="New Topic Name",
        description="Topic name to be created",
        default="Blender Chat",
    )
    num_conditions: bpy.props.IntProperty(
        name="Num Conditions",
        description="Number of conditions for the conversation",
        default=1,
        min=0,
        max=10,
    )

    def get_topics(self, _):
        topic_dir = f"{CHAT_DATA_DIR}/topics"
        if not os.path.isdir(topic_dir):
            return []

        items = []
        topic_files = glob.glob(f"{topic_dir}/**/*.json", recursive=True)
        for file in topic_files:
            topic_name = os.path.splitext(os.path.basename(file))[0]
            items.append((topic_name, topic_name, file))
        return items

    topic: bpy.props.EnumProperty(
        name="Topic",
        description="Topic",
        items=get_topics,
    )


class OPENAI_ChatToolConditions(bpy.types.PropertyGroup):
    condition: bpy.props.StringProperty(
        name="Condition",
        description="Condition for the conversation",
    )


class OPENAI_CodeToolGenerateCodeProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Prompt",
    )
    input_method: bpy.props.EnumProperty(
        name="Input Method",
        description="Method to input the prompt",
        items=[
            ('TEXT', "Text", "Input from text"),
            ('AUDIO', "Audio", "Input from audio"),
        ],
        default='TEXT',
    )
    num_conditions: bpy.props.IntProperty(
        name="Num Conditions",
        description="Number of conditions for the code generation",
        default=1,
        min=0,
        max=10,
    )


class OPENAI_CodeToolEditCodeProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Prompt",
    )
    num_conditions: bpy.props.IntProperty(
        name="Number of Conditions",
        description="Number of conditions for the code generation",
        default=1,
        min=0,
        max=10,
    )


class OPENAI_CodeToolConditions(bpy.types.PropertyGroup):
    condition: bpy.props.StringProperty(
        name="Condition",
        description="Condition for the conversation",
    )


class OPENAI_UsageStatisticsImageTool(bpy.types.PropertyGroup):
    images_1024x1024: bpy.props.IntProperty(
        name="1024x1024 Images",
        description="How many generated images whose size is 1024x1024",
        default=0,
    )
    images_512x512: bpy.props.IntProperty(
        name="512x512 Images",
        description="How many generated images whose size is 512x512",
        default=0,
    )
    images_256x256: bpy.props.IntProperty(
        name="256x256 Images",
        description="How many generated images whose size is 256x256",
        default=0,
    )


class OPENAI_UsageStatisticsAudioTool(bpy.types.PropertyGroup):
    seconds_whisper: bpy.props.IntProperty(
        name="Whisper Seconds",
        description="How many seconds of transcribed audio",
        default=0,
    )


class OPENAI_UsageStatisticsChatTool(bpy.types.PropertyGroup):
    tokens_gpt35_turbo: bpy.props.IntProperty(
        name="GPT-3.5 Turbo Tokens",
        description="How many generated token from the 'GPT-3.5 Turobo' model",
        default=0,
    )
    tokens_gpt4_8k: bpy.props.IntProperty(
        name="GPT-4 8K Tokens",
        description="How many generated token from the 'GPT-4 8K' model",
        default=0,
    )
    tokens_gpt4_32k: bpy.props.IntProperty(
        name="GPT-4 32K Tokens",
        description="How many generated token from the 'GPT-4 32K' model",
        default=0,
    )


class OPENAI_UsageStatisticsCodeTool(bpy.types.PropertyGroup):
    tokens_gpt35_turbo: bpy.props.IntProperty(
        name="GPT-3.5 Turbo Tokens",
        description="How many generated token from the 'GPT-3.5 Turobo' model",
        default=0,
    )
    tokens_gpt4_8k: bpy.props.IntProperty(
        name="GPT-4 8K Tokens",
        description="How many generated token from the 'GPT-4 8K' model",
        default=0,
    )
    tokens_gpt4_32k: bpy.props.IntProperty(
        name="GPT-4 32K Tokens",
        description="How many generated token from the 'GPT-4 32K' model",
        default=0,
    )


def register_properties():
    scene = bpy.types.Scene

    bpy.utils.register_class(OPENAI_ImageToolGenerateImageProperties)
    bpy.utils.register_class(OPENAI_ImageToolEditImageProperties)
    bpy.utils.register_class(OPENAI_ImageToolGenerateVariationImageProperties)
    bpy.utils.register_class(OPENAI_ImageToolGeneratedImagesProperties)
    bpy.utils.register_class(OPENAI_AudioToolTranscribeSoundStripProperties)
    bpy.utils.register_class(OPENAI_AudioToolTranscribeAudioFileProperties)
    bpy.utils.register_class(OPENAI_ChatToolProperties)
    bpy.utils.register_class(OPENAI_ChatToolConditions)
    bpy.utils.register_class(OPENAI_CodeToolGenerateCodeProperties)
    bpy.utils.register_class(OPENAI_CodeToolConditions)
    bpy.utils.register_class(OPENAI_CodeToolEditCodeProperties)
    bpy.utils.register_class(OPENAI_UsageStatisticsImageTool)
    bpy.utils.register_class(OPENAI_UsageStatisticsAudioTool)
    bpy.utils.register_class(OPENAI_UsageStatisticsChatTool)
    bpy.utils.register_class(OPENAI_UsageStatisticsCodeTool)

    scene.openai_icon_collection = bpy.utils.previews.new()
    scene.openai_icon_collection.load(
        "openai_base", f"{ICON_DIR}/openai_base.png", 'IMAGE')

    # Properties for Image Tool.
    scene.openai_image_tool_generate_image_props = bpy.props.PointerProperty(
        type=OPENAI_ImageToolGenerateImageProperties,
    )
    scene.openai_image_tool_image_collection = bpy.utils.previews.new()
    scene.openai_image_tool_edit_image_props = bpy.props.PointerProperty(
        type=OPENAI_ImageToolEditImageProperties,
    )
    scene.openai_image_tool_edit_image_base_image = bpy.props.PointerProperty(
        name="Base Image",
        description="Image block to be used for the base image",
        type=bpy.types.Image,
        poll=lambda _, img: img.depth // (img.is_float * 3 + 1) == 32,
    )
    scene.openai_image_tool_edit_image_mask_image = bpy.props.PointerProperty(
        name="Mask Image",
        description="Image block to be used for the mask image",
        type=bpy.types.Image,
        poll=lambda _, img: img.depth // (img.is_float * 3 + 1) == 32,
    )
    scene.openai_image_tool_generate_variation_image_props = \
        bpy.props.PointerProperty(
            type=OPENAI_ImageToolGenerateVariationImageProperties
        )
    scene.openai_image_tool_generate_variation_image_base_image = \
        bpy.props.PointerProperty(
            name="Base Image",
            description="Image block to be used for the base image",
            type=bpy.types.Image,
            poll=lambda _, img: img.depth // (img.is_float * 3 + 1) == 32,
        )
    scene.openai_image_tool_generated_images_props = bpy.props.PointerProperty(
        type=OPENAI_ImageToolGeneratedImagesProperties,
    )

    # Properties for Audio Tool.
    scene.openai_audio_tool_transcribe_sound_strip_props = \
        bpy.props.PointerProperty(
            type=OPENAI_AudioToolTranscribeSoundStripProperties,
        )
    scene.openai_audio_tool_transcribe_audio_file_props = \
        bpy.props.PointerProperty(
            type=OPENAI_AudioToolTranscribeAudioFileProperties,
        )
    scene.openai_audio_tool_target_text_block = bpy.props.PointerProperty(
        name="Target Text Block",
        description="""Name of target text block to where the transcript is
saved""",
        type=bpy.types.Text,
    )
    scene.openai_audio_tool_sound_data_block = \
        bpy.props.PointerProperty(
            name="Sound Data Block",
            description="Sound data block to be transcribed",
            type=bpy.types.Sound,
        )

    # Properties for Chat Tool.
    scene.openai_chat_tool_props = bpy.props.PointerProperty(
        type=OPENAI_ChatToolProperties,
    )
    scene.openai_chat_tool_conditions = bpy.props.CollectionProperty(
        name="Conditions",
        type=OPENAI_ChatToolConditions,
    )

    # Properties for Code Tool.
    scene.openai_code_tool_props = bpy.props.PointerProperty(
        type=OPENAI_CodeToolGenerateCodeProperties,
    )
    scene.openai_code_tool_conditions = bpy.props.CollectionProperty(
        name="Conditions",
        description="Conditions",
        type=OPENAI_CodeToolConditions,
    )
    scene.openai_code_tool_generate_code_props = bpy.props.PointerProperty(
        type=OPENAI_CodeToolGenerateCodeProperties,
    )
    scene.openai_code_tool_generate_code_conditions = \
        bpy.props.CollectionProperty(
            name="Conditions",
            description="Conditions",
            type=OPENAI_CodeToolConditions,
        )
    scene.openai_code_tool_edit_code_props = bpy.props.PointerProperty(
        type=OPENAI_CodeToolEditCodeProperties,
    )
    scene.openai_code_tool_edit_code_conditions = bpy.props.CollectionProperty(
        name="Conditions",
        description="Conditions",
        type=OPENAI_CodeToolConditions,
    )
    scene.openai_code_tool_edit_code_text_block = \
        bpy.props.PointerProperty(
            name="Text Block",
            description="Text Block to edit",
            type=bpy.types.Text,
        )

    # Properties for the usage statistics.
    scene.openai_usage_statistics_image_tool = bpy.props.PointerProperty(
        name="Usage Statistics for Image Tool",
        type=OPENAI_UsageStatisticsImageTool,
    )
    scene.openai_usage_statistics_audio_tool = bpy.props.PointerProperty(
        name="Usage Statistics for Audio Tool",
        type=OPENAI_UsageStatisticsAudioTool,
    )
    scene.openai_usage_statistics_chat_tool = bpy.props.PointerProperty(
        name="Usage Statistics for Chat Tool",
        type=OPENAI_UsageStatisticsChatTool,
    )
    scene.openai_usage_statistics_code_tool = bpy.props.PointerProperty(
        name="Usage Statistics for Code Tool",
        type=OPENAI_UsageStatisticsCodeTool,
    )


def unregister_properties():
    scene = bpy.types.Scene

    bpy.utils.previews.remove(scene.openai_icon_collection)
    bpy.utils.previews.remove(scene.openai_image_tool_image_collection)

    del scene.openai_usage_statistics_code_tool
    del scene.openai_usage_statistics_chat_tool
    del scene.openai_usage_statistics_audio_tool
    del scene.openai_usage_statistics_image_tool

    del scene.openai_code_tool_edit_code_text_block
    del scene.openai_code_tool_edit_code_conditions
    del scene.openai_code_tool_edit_code_props
    del scene.openai_code_tool_generate_code_conditions
    del scene.openai_code_tool_generate_code_props
    del scene.openai_code_tool_conditions
    del scene.openai_code_tool_props

    del scene.openai_chat_tool_conditions
    del scene.openai_chat_tool_props

    del scene.openai_image_tool_generated_images_props
    del scene.openai_image_tool_generate_variation_image_base_image
    del scene.openai_image_tool_generate_variation_image_props
    del scene.openai_image_tool_edit_image_mask_image
    del scene.openai_image_tool_edit_image_base_image
    del scene.openai_image_tool_edit_image_props
    del scene.openai_image_tool_generate_image_props
    del scene.openai_image_tool_image_collection

    del scene.openai_audio_tool_sound_data_block
    del scene.openai_audio_tool_target_text_block
    del scene.openai_audio_tool_transcribe_audio_file_props
    del scene.openai_audio_tool_transcribe_sound_strip_props

    del scene.openai_icon_collection

    bpy.utils.unregister_class(OPENAI_UsageStatisticsCodeTool)
    bpy.utils.unregister_class(OPENAI_UsageStatisticsChatTool)
    bpy.utils.unregister_class(OPENAI_UsageStatisticsAudioTool)
    bpy.utils.unregister_class(OPENAI_UsageStatisticsImageTool)
    bpy.utils.unregister_class(OPENAI_CodeToolEditCodeProperties)
    bpy.utils.unregister_class(OPENAI_CodeToolConditions)
    bpy.utils.unregister_class(OPENAI_CodeToolGenerateCodeProperties)
    bpy.utils.unregister_class(OPENAI_ChatToolConditions)
    bpy.utils.unregister_class(OPENAI_ChatToolProperties)
    bpy.utils.unregister_class(OPENAI_AudioToolTranscribeAudioFileProperties)
    bpy.utils.unregister_class(OPENAI_AudioToolTranscribeSoundStripProperties)
    bpy.utils.unregister_class(OPENAI_ImageToolGeneratedImagesProperties)
    bpy.utils.unregister_class(
        OPENAI_ImageToolGenerateVariationImageProperties)
    bpy.utils.unregister_class(OPENAI_ImageToolEditImageProperties)
    bpy.utils.unregister_class(OPENAI_ImageToolGenerateImageProperties)
