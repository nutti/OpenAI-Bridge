import bpy


def register_properties():
    scene = bpy.types.Scene

    scene.openai_audio_target_text_object = bpy.props.PointerProperty(
        name="Target Text Object",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'FONT',
    )
    scene.openai_audio_target_text = bpy.props.PointerProperty(
        name="Target Text",
        type=bpy.types.Text,
    )


def unregister_properties():
    scene = bpy.types.Scene

    del scene.openai_audio_target_text
    del scene.openai_audio_target_text_object
