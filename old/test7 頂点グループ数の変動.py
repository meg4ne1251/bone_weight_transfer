import bpy

class OBJECT_PT_dynamic_vertex_group_selector(bpy.types.Panel):
    bl_label = "Dynamic Vertex Group Selector"
    bl_idname = "OBJECT_PT_dynamic_vertex_group_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vertex Groups"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.object

        layout.prop(scene, "vertex_group_count")  # 数字を入力するボックス

        if obj and obj.type == 'MESH':
            for i in range(scene.vertex_group_count):
                # 動的に頂点グループの選択プロパティを生成
                layout.prop_search(
                    obj, f"active_vertex_group_{i}", obj, "vertex_groups", text=f"Vertex Group {i+1}"
                )
        else:
            layout.label(text="No mesh object selected.")

def register():
    bpy.utils.register_class(OBJECT_PT_dynamic_vertex_group_selector)
    
    # 数字の入力プロパティ
    bpy.types.Scene.vertex_group_count = bpy.props.IntProperty(
        name="Vertex Group Count",
        default=1,
        min=1,
        description="Number of vertex groups to display"
    )
    
    # 動的に頂点グループプロパティを生成
    for i in range(10):  # 最大10個まで対応（必要に応じて変更可能）
        setattr(bpy.types.Object, f"active_vertex_group_{i}", bpy.props.StringProperty())

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_dynamic_vertex_group_selector)
    
    del bpy.types.Scene.vertex_group_count

    # 登録したプロパティを解除
    for i in range(10):
        delattr(bpy.types.Object, f"active_vertex_group_{i}")

if __name__ == "__main__":
    register()
