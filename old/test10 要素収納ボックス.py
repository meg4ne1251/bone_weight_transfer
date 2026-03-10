import bpy

# A property group to hold the expand/collapse state
class MySettings(bpy.types.PropertyGroup):
    expand_section: bpy.props.BoolProperty(
        name="Expand Section",
        description="Expand or collapse section",
        default=False
    )

class ExpandablePanelOperator(bpy.types.Operator):
    bl_idname = "wm.expandable_ui_layout"
    bl_label = "Expandable UI Layout"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        my_settings = context.scene.my_settings

        # Use a box to create a visual container for the section
        box = layout.box()

        # Create the expandable/collapsible section
        row = box.row()
        row.prop(my_settings, "expand_section", icon="TRIA_DOWN" if my_settings.expand_section else "TRIA_RIGHT", 
                 icon_only=True, emboss=False)
        row.label(text="Details")

        # Only show content if expanded
        if my_settings.expand_section:
            sub_box = box.box()  # Nested box for the expanded content
            sub_box.label(text="Expanded Element 1")
            sub_box.operator("object.select_all", text="Select All")
            sub_box.prop(context.scene, "frame_start", text="Frame Start")
            sub_box.prop(context.scene, "frame_end", text="Frame End")

# Panel to activate the custom operator
class ExpandablePanel(bpy.types.Panel):
    bl_label = "Expandable UI Layout"
    bl_idname = "VIEW3D_PT_expandable_ui_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UI Layout'

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.expandable_ui_layout", text="Open Expandable UI")

# Registration
classes = [MySettings, ExpandablePanelOperator, ExpandablePanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_settings = bpy.props.PointerProperty(type=MySettings)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.my_settings

if __name__ == "__main__":
    register()
