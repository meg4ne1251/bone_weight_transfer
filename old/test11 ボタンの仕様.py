import bpy

# オペレーター1: ボタン1用
class SimpleOperator1(bpy.types.Operator):
    bl_idname = "wm.simple_operator_1"
    bl_label = "Print Message 1"

    def execute(self, context):
        print("ボタン1が押されました")
        return {'FINISHED'}

# オペレーター2: ボタン2用
class SimpleOperator2(bpy.types.Operator):
    bl_idname = "wm.simple_operator_2"
    bl_label = "Print Message 2"

    def execute(self, context):
        print("ボタン2が押されました")
        return {'FINISHED'}

# オペレーター3: ボタン3用
class SimpleOperator3(bpy.types.Operator):
    bl_idname = "wm.simple_operator_3"
    bl_label = "Print Message 3"

    def execute(self, context):
        print("ボタン3が押されました")
        return {'FINISHED'}

# パネルクラス: 3つのボタンを配置
class SimplePanel(bpy.types.Panel):
    bl_label = "Multiple Buttons"
    bl_idname = "PT_SimplePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Simple Addon'

    def draw(self, context):
        layout = self.layout
        
        # 各ボタンをオペレーターに紐付けて配置
        layout.operator("wm.simple_operator_1", text="Button 1")
        layout.operator("wm.simple_operator_2", text="Button 2")
        layout.operator("wm.simple_operator_3", text="Button 3")

# クラスの登録と解除
def register():
    bpy.utils.register_class(SimpleOperator1)
    bpy.utils.register_class(SimpleOperator2)
    bpy.utils.register_class(SimpleOperator3)
    bpy.utils.register_class(SimplePanel)

def unregister():
    bpy.utils.unregister_class(SimpleOperator1)
    bpy.utils.unregister_class(SimpleOperator2)
    bpy.utils.unregister_class(SimpleOperator3)
    bpy.utils.unregister_class(SimplePanel)

if __name__ == "__main__":
    register()
