import bpy

from ..op import image


class OPENAI_PT_GenerateImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Generate Image"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_props

        row = layout.row(align=True)
        row.operator_context = 'EXEC_DEFAULT'
        row.prop(props, "prompt", text="")
        ops = row.operator(image.OPENAI_OT_GeneateImage.bl_idname, icon='PLAY', text="")
        ops.prompt = props.prompt
        ops.num_images = props.num_images
        ops.image_size = props.image_size
        ops.auto_image_name = props.auto_image_name
        ops.image_name = props.image_name

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Size:")
        col.prop(props, "image_size", text="")
        col = row.column(align=True)
        col.label(text="Num")
        col.prop(props, "num_images", text="")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text="Name:")
        row.prop(props, "auto_image_name", text="Auto")
        r = col.row(align=True)
        r.prop(props, "image_name", text="")
        r.enabled = not props.auto_image_name


class OPENAI_PT_EditImage(bpy.types.Panel):

    bl_region_type = 'UI'
    bl_space_type = 'IMAGE_EDITOR'
    bl_category = "OpenAI"
    bl_label = "Edit Image"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        props = sc.openai_image_tool_props

        row = layout.row(align=True)
        row.template_icon_view(props, "edit_target", show_labels=True)
        col = row.column(align=True)
        op = col.operator(image.OPENAI_OT_LoadImage.bl_idname, text="", icon='IMAGE_DATA')
        op.image_filepath = props.edit_target
        op = col.operator(image.OPENAI_OT_RemoveImage.bl_idname, text="", icon='TRASH')
        op.image_filepath = props.edit_target

        # TODO: Add editing tool
