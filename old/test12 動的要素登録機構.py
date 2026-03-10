import bpy

# 数字プロパティを定義し、updateにコールバック関数を設定
class MyAddonProperties(bpy.types.PropertyGroup):
    my_prop: bpy.props.IntProperty(
        name="My Prop",
        default=1,
        min=0,
        max=10,
        update=lambda self, context: self.prop_changed(context)
    )

    # プロパティが変更されたときに呼び出される関数
    def prop_changed(self, context):
        print(f"プロパティが変更されました: {self.my_prop}")

# UIパネル
class MyAddonPanel(bpy.types.Panel):
    bl_label = "My Addon Panel"
    bl_idname = "OBJECT_PT_my_addon"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'My Addon'

    def draw(self, context):
        layout = self.layout
        props = context.scene.my_addon_props

        # プロパティを表示
        layout.prop(props, "my_prop")

# アドオン登録
def register():
    bpy.utils.register_class(MyAddonProperties)
    bpy.utils.register_class(MyAddonPanel)
    bpy.types.Scene.my_addon_props = bpy.props.PointerProperty(type=MyAddonProperties)

def unregister():
    bpy.utils.unregister_class(MyAddonPanel)
    bpy.utils.unregister_class(MyAddonProperties)
    del bpy.types.Scene.my_addon_props

if __name__ == "__main__":
    register()
