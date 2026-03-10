import bpy

class OBJECT_PT_vertex_group_selector(bpy.types.Panel):
    bl_label = "Vertex Group Selector"
    bl_idname = "OBJECT_PT_vertex_group_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vertex Groups"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.type == 'MESH':  # メッシュオブジェクトかどうかを確認
            layout.label(text="Select Vertex Group:")
            layout.prop_search(
                obj, "active_vertex_group", obj, "vertex_groups", text=""
            )
        else:
            layout.label(text="No mesh object selected.")

# 選択した頂点グループを管理するためのプロパティを追加
def register():
    bpy.types.Object.active_vertex_group = bpy.props.StringProperty()
    bpy.utils.register_class(OBJECT_PT_vertex_group_selector)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_vertex_group_selector)
    del bpy.types.Object.active_vertex_group

if __name__ == "__main__":
    register()
