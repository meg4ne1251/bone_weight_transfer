import bpy
from bpy.types import Context


# bone転送を実行するオペレーション
class Start_operator(bpy.types.Operator):
    bl_idname = "wm.start_operator"
    bl_label = "Start Exchange Bone Weight"

    def execute(self, context: Context):
        
        for i in range(context.scene.vertex_group_count):
            mod = bpy.context.active_object.modifiers.new(name="頂点ウェイト合成", type='VERTEX_WEIGHT_MIX')
            mod.mix_mode = 'SET'
            mod.mix_set = "B"

            mod.vertex_group_a = getattr(bpy.context.object, f"active_vertex_group_{i}_R", None) #コピー先の頂点データを指定　ここでのgetattr関数は、for文を用いて動的に変更される変数を取得するためにある　blender限定関数
            mod.vertex_group_b = getattr(bpy.context.object, f"active_vertex_group_{i}_L", None) #コピー元の頂点データを指定  つまり、bpy.context.object.active.vetex.group....　に連続でアクセスしていることと等しい。
            bpy.ops.object.modifier_apply(modifier = "頂点ウェイト合成", report = True) #モディファイアを適用


#今日はここまで　これで大台の複数同時転送が可能になった。可能なら、元bone2複数に対して、先bone1のような状況でも使えるようにしたい　また、変数の数によって、登録、末梢の動的化ができるなら試してみたい。　UIの修正　ハンバーガメニュータイプもやってみたい
  
        self.report({'INFO'}, "頂点データを転送しました")
        print(context.scene.vertex_group_count)
        return {'FINISHED'}
# すべての頂点グループを削除するオペレーション
class Deleat_operator(bpy.types.Operator):
    bl_idname = "wm.deleat_operator"
    bl_label = "deleat all vertex group"

    def execute(self, context: Context):
        obj = context.active_object
        if obj.vertex_groups:
            context.active_object.vertex_groups.clear()
            self.report({'INFO'}, "すべての頂点グループを削除しました")
        else:
            self.report({'INFO'}, "頂点グループが存在しません")
        return{'FINISHED'}
    

# カウントの変更に応じて、変数をblenderに登録する関数



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

        layout.separator() #線入れるやつ

        if obj and obj.type == 'MESH':
            for i in range(scene.vertex_group_count):
                row = layout.row() #ここで宣言することで、毎回下にずれていくようになる。
                # 動的に頂点グループの選択プロパティを生成
                row.prop_search( #これが、検索機能付き選択ボックスを呼び出す関数
                    obj, f"active_vertex_group_{i}_L", obj, "vertex_groups", text=f"元 {i+1} L"
                )
                row.prop_search(
                    obj, f"active_vertex_group_{i}_R", obj, "vertex_groups", text=f"先 {i+1} R"
                )

                
        else:
            layout.label(text="No mesh object selected.")
            
        layout.separator_spacer()
        layout.operator("wm.start_operator", text="Run")
        layout.separator()
        layout.operator("wm.deleat_operator", text="Clear Vertex Group")

        

def register():
    bpy.utils.register_class(OBJECT_PT_dynamic_vertex_group_selector)
    bpy.utils.register_class(Start_operator)
    bpy.utils.register_class(Deleat_operator)
    
    # 数字の入力プロパティ
    bpy.types.Scene.vertex_group_count = bpy.props.IntProperty(
        name="Vertex Group Count",
        default=1,
        min=1,
        description="Number of vertex groups to display"
    )
    
    # 動的に頂点グループプロパティを生成
    for i in range(10):  # 最大10個まで対応（必要に応じて変更可能）
        setattr(bpy.types.Object, f"active_vertex_group_{i}_L", bpy.props.StringProperty())
        setattr(bpy.types.Object, f"active_vertex_group_{i}_R", bpy.props.StringProperty())

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_dynamic_vertex_group_selector)
    bpy.utils.unregister_class(Start_operator)
    bpy.utils.unregister_class(Deleat_operator)
    
    del bpy.types.Scene.vertex_group_count

    # 登録したプロパティを解除
    for i in range(10):
        delattr(bpy.types.Object, f"active_vertex_group_{i}_L")
        delattr(bpy.types.Object, f"active_vertex_group_{i}_R")
        

if __name__ == "__main__":
    register()
