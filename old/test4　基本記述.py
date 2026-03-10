#Blenderアドオンの基本的な記述方法


import bpy   # アドオン開発者に対して用意しているAPIを利用する


# アドオンに関する情報を保持する、bl_info変数
bl_info = {
    "name": "サンプル 2-1: オブジェクトを生成するアドオン",
    "author": "ぬっち（Nutti）",
    "version": (3, 0),
    "blender": (2, 80, 0),
    "location": "3Dビューポート > 追加 > メッシュ",
    "description": "オブジェクトを生成するサンプルアドオン",
    "warning": "",
    "support": "TESTING",
    "doc_url": "",
    "tracker_url": "",
    "category": "Object"
}


# オブジェクト（ICO球）を生成するオペレータ
class SAMPLE21_OT_CreateObject(bpy.types.Operator):

    bl_idname = "object.sample21_create_object"
    bl_label = "球"
    bl_description = "ICO球を追加します"
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれる関数
    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=2.0, location=(5.0, -5.0, 0.0), rotation=(0.79, 0.0, 1.57))
        print("サンプル 2-1: ICO球を生成しました。")

        return {'FINISHED'}


# メニューを構築する関数
def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(SAMPLE21_OT_CreateObject.bl_idname)

# Blenderに登録するクラス
classes = [
    SAMPLE21_OT_CreateObject,
]

# アドオン有効化時の処理
def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_fn)
    print("サンプル 2-1: アドオン『サンプル 2-1』が有効化されました。")


# アドオン無効化時の処理
def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)
    print("サンプル 2-1: アドオン『サンプル 2-1』が無効化されました。")


# メイン処理
if __name__ == "__main__":
    unregister()