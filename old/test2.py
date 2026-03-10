import bpy

class OBJECT_OT_AddVertexWeightMixModifier(bpy.types.Operator):
    bl_idname = "object.add_vertex_weight_mix_modifier"
    bl_label = "Add Vertex Weight Mix Modifier"
    bl_description = "VERTEX_WEIGHT_MIXモディファイアを追加し、頂点グループを設定する"
    bl_options = {'REGISTER', 'UNDO'}

    vertex_group_a: bpy.props.StringProperty(name="Vertex Group A")
    vertex_group_b: bpy.props.StringProperty(name="Vertex Group B")
    
    def execute(self, context):
        obj = context.active_object

        if obj and obj.type == 'MESH':
            # VERTEX_WEIGHT_MIXモディファイアを追加
            mod = obj.modifiers.new(name="頂点ウェイト合成", type='VERTEX_WEIGHT_MIX')
            
            # 選択された頂点グループを設定
            mod.vertex_group_a = self.vertex_group_a
            mod.vertex_group_b = self.vertex_group_b
            
            self.report({'INFO'}, "VERTEX_WEIGHT_MIXモディファイアが追加されました。")
        else:
            self.report({'WARNING'}, "メッシュオブジェクトを選択してください。")
        
        return {'FINISHED'}

class OBJECT_PT_VertexWeightMixPanel(bpy.types.Panel):
    bl_label = "Vertex Weight Mix Settings"
    bl_idname = "OBJECT_PT_vertex_weight_mix"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "modifier"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.type == 'MESH' and obj.vertex_groups:
            layout.label(text="Vertex Weight Mix Modifier Settings")

            row = layout.row()
            row.prop_search(self, "vertex_group_a", obj, "vertex_groups", text="Vertex Group A")

            row = layout.row()
            row.prop_search(self, "vertex_group_b", obj, "vertex_groups", text="Vertex Group B")

            layout.operator("object.add_vertex_weight_mix_modifier")
        else:
            layout.label(text="メッシュオブジェクトを選択し、頂点グループを設定してください。")

def register():
    bpy.utils.register_class(OBJECT_OT_AddVertexWeightMixModifier)
    bpy.utils.register_class(OBJECT_PT_VertexWeightMixPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_AddVertexWeightMixModifier)
    bpy.utils.unregister_class(OBJECT_PT_VertexWeightMixPanel)

if __name__ == "__main__":
    register()
