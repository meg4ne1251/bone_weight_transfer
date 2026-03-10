import bpy

class OBJECT_OT_generate_rectangles(bpy.types.Operator):
    """長方形メッシュを生成"""
    bl_idname = "object.generate_rectangles"
    bl_label = "Generate Rectangles"

    def execute(self, context):
        count = context.scene.rectangle_count  # 入力された数値を取得
        for i in range(count):
            # 長方形メッシュを生成
            bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(i * 3, 0, 0))
            plane = bpy.context.active_object
            plane.scale = (2, 1, 1)  # 長方形にスケーリング
        return {'FINISHED'}

class OBJECT_PT_rectangle_generator(bpy.types.Panel):
    """UIパネル"""
    bl_label = "Rectangle Generator"
    bl_idname = "OBJECT_PT_rectangle_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rectangle Generator"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "rectangle_count")  # 数値入力ボックス
        layout.operator("object.generate_rectangles")  # ボタン

def register():
    bpy.utils.register_class(OBJECT_OT_generate_rectangles)
    bpy.utils.register_class(OBJECT_PT_rectangle_generator)
    bpy.types.Scene.rectangle_count = bpy.props.IntProperty(
        name="Rectangle Count",
        default=1,
        min=1,
        description="生成する長方形の数"
    )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_generate_rectangles)
    bpy.utils.unregister_class(OBJECT_PT_rectangle_generator)
    del bpy.types.Scene.rectangle_count

if __name__ == "__main__":
    register()
