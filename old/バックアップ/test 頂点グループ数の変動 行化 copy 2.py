import bpy
from bpy.types import Context

maxCount = 1
afterCount = 1

# bone転送を実行するオペレーション
class Start_operator(bpy.types.Operator):
    bl_idname = "wm.start_operator"
    bl_label = "Start Exchange Bone Weight"

    def execute(self, context: Context):
        

        for i in range(context.scene.vertex_group_count.vertex_group_count):
            #モディファイアが適用できるか判定
            if getattr(bpy.context.object, f"active_vertex_group_{i}_R", None) and getattr(bpy.context.object, f"active_vertex_group_{i}_L", None):
                #同じ名前のモディファイア存在したら、そいつをよけて実行する仕組みを作る
                mod = bpy.context.active_object.modifiers.new(name="頂点ウェイト合成_mede_by_AddOn", type='VERTEX_WEIGHT_MIX')
                mod.mix_mode = 'SET'
                mod.mix_set = "B"
                mod.vertex_group_a = getattr(bpy.context.object, f"active_vertex_group_{i}_R", None) #コピー先の頂点データを指定　ここでのgetattr関数は、for文を用いて動的に変更される変数を取得するためにある　blender限定関数
                mod.vertex_group_b = getattr(bpy.context.object, f"active_vertex_group_{i}_L", None) #コピー元の頂点データを指定  つまり、bpy.context.object.active.vetex.group....　に連続でアクセスしていることと等しい。
                print(mod.vertex_group_b)
                bpy.ops.object.modifier_apply(modifier = "頂点ウェイト合成_mede_by_AddOn", report = True) #モディファイアを適用
                self.report({'INFO'}, f"{i+1}組めの頂点データを転送しました")
            else:
                self.report({'ERROR'}, f"{i+1}組めの頂点グループが選択されていません")


#今日はここまで　これで大台の複数同時転送が可能になった。可能なら、元bone2複数に対して、先bone1のような状況でも使えるようにしたい　また、変数の数によって、登録、末梢の動的化ができるなら試してみたい。　UIの修正　ハンバーガメニュータイプもやってみたい
  
        
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
    

# カウントの変更に応じて、プロパティをblenderに登録する関数
class Change_vertex_group_count(bpy.types.PropertyGroup):
    vertex_group_count: bpy.props.IntProperty(
        name="Vertex Group Count",
        default=1,
        min=1,
        max=20,
        update=lambda self, context: self.prop_changes(context)
    )

    def prop_changes(self, context):

        count = context.scene.vertex_group_count.vertex_group_count

        for i in range(count):
            setattr(bpy.types.Object, f"active_vertex_group_{i}_L", bpy.props.StringProperty())
            setattr(bpy.types.Object, f"active_vertex_group_{i}_R", bpy.props.StringProperty())
            setattr(bpy.types.Object, f"active_vertex_group_{i}_count", bpy.props.IntProperty(
                name="Copy Vertex Group Count",
                description="Enter number fo copy vertex group",
                default=1,
                min=1,
                max=10
                )
            )

#今日はここまで、動的にプロパティを登録する機構はできた。次は、1;多数の場合と、UIの編集かな
        if count>maxCount: maxCount=count

        print(f"プロパティが変更されました:{count}")

#今はここまで、処理を実行するときにコピー元の頂点グループを削除するか聞く機能があっても面白そう　UIの方は、動的にpropを生成できるかですべてが決まるね

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

        layout.prop(scene.vertex_group_count, "vertex_group_count")  # 数字を入力するボックス

        layout.separator() #線入れるやつ

        if obj and obj.type == 'MESH':
            for i in range(scene.vertex_group_count.vertex_group_count):
                box = layout.box()
                box.label(text=f"組み合わせ{i+1}")
                
                # 動的に頂点グループの選択プロパティを生成
                mini_box_1= box.box()
                mini_box_1.label(text="コピー先頂点グループ")
                mini_box_1.prop_search( #これが、検索機能付き選択ボックスを呼び出す関数
                    obj, f"active_vertex_group_{i}_R", obj, "vertex_groups", text=""
                )

                mini_box_2= box.box()
                mini_box_2.label(text="コピー元頂点グループ")
                mini_box_2.prop(obj, f"active_vertex_group_{i}_count")  # 数字を入力するボックス
                mini_box_2.prop_search(
                    obj, f"active_vertex_group_{i}_L", obj, "vertex_groups", text=""
                )


            layout.separator_spacer()
            layout.operator("wm.start_operator", text="Run")
            layout.separator()
            layout.operator("wm.deleat_operator", text="Clear all Vertex Group")

                
        else:
            layout.label(text="No mesh object selected.")
            

        

def register():
    bpy.utils.register_class(OBJECT_PT_dynamic_vertex_group_selector)
    bpy.utils.register_class(Start_operator)
    bpy.utils.register_class(Deleat_operator)
    bpy.utils.register_class(Change_vertex_group_count)
    
    # 数字の入力プロパティ
    bpy.types.Scene.vertex_group_count = bpy.props.PointerProperty(type=Change_vertex_group_count)
    setattr(bpy.types.Object, f"active_vertex_group_0_L", bpy.props.StringProperty())
    setattr(bpy.types.Object, f"active_vertex_group_0_R", bpy.props.StringProperty())
    setattr(bpy.types.Object, f"active_vertex_group_0_count", bpy.props.IntProperty(
        name="Copy Vertex Group Count",
        description="Enter number fo copy vertex group",
        default=1,
        min=1,
        max=10
        )
    )
 
    # 動的に頂点グループプロパティを生成
#    for i in range(10):  # 最大10個まで対応（必要に応じて変更可能）
#        setattr(bpy.types.Object, f"active_vertex_group_{i}_L", bpy.props.StringProperty())
#        setattr(bpy.types.Object, f"active_vertex_group_{i}_R", bpy.props.StringProperty())

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_dynamic_vertex_group_selector)
    bpy.utils.unregister_class(Start_operator)
    bpy.utils.unregister_class(Deleat_operator)
    
    del bpy.types.Scene.vertex_group_count

    # 登録したプロパティを解除
    for i in range(beforeCount):
        delattr(bpy.types.Object, f"active_vertex_group_{i}_L")
        delattr(bpy.types.Object, f"active_vertex_group_{i}_R")
        delattr(bpy.types.Object, f"active_vertex_group_{i}_count")
        

if __name__ == "__main__":
    register()
