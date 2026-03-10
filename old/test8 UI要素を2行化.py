import bpy

class SplitRowsOperator(bpy.types.Operator):
    bl_idname = "wm.split_rows_operator"
    bl_label = "Split Rows Example"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout

        # First row of elements
        row = layout.row()
        row.label(text="First Row, Element 1")
        row.operator("object.select_all", text="Select All")

        # Second row of elements
        row = layout.row()
        row.prop(context.scene, "frame_start", text="Frame Start")
        row.prop(context.scene, "frame_end", text="Frame End")

# Panel to activate the custom operator
class SplitRowsPanel(bpy.types.Panel):
    bl_label = "Split Rows UI"
    bl_idname = "VIEW3D_PT_split_rows_ui"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Row Layout'

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.split_rows_operator", text="Open Split Rows UI")


# Registration
classes = [SplitRowsOperator, SplitRowsPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()