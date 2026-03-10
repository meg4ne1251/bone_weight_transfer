import bpy
import re
from bpy.types import Context

# プロパティの最大数（register時に一括登録）
MAX_VERTEX_GROUP_PAIRS = 20

# 左右ミラー検出用のパターン定義
# (正規表現, ミラー先の置換パターン, 元に戻す置換パターン)
MIRROR_PATTERNS = [
    # suffix: .L / .R
    (re.compile(r'^(.+)\.L$', re.IGNORECASE), r'\1.R', r'\1.L'),
    (re.compile(r'^(.+)\.R$', re.IGNORECASE), r'\1.L', r'\1.R'),
    # suffix: _L / _R
    (re.compile(r'^(.+)_L$', re.IGNORECASE), r'\1_R', r'\1_L'),
    (re.compile(r'^(.+)_R$', re.IGNORECASE), r'\1_L', r'\1_R'),
    # suffix: _left / _right
    (re.compile(r'^(.+)_left$', re.IGNORECASE), r'\1_right', r'\1_left'),
    (re.compile(r'^(.+)_right$', re.IGNORECASE), r'\1_left', r'\1_right'),
    # suffix: .left / .right
    (re.compile(r'^(.+)\.left$', re.IGNORECASE), r'\1.right', r'\1.left'),
    (re.compile(r'^(.+)\.right$', re.IGNORECASE), r'\1.left', r'\1.right'),
    # prefix: L_ / R_
    (re.compile(r'^L_(.+)$', re.IGNORECASE), r'R_\1', r'L_\1'),
    (re.compile(r'^R_(.+)$', re.IGNORECASE), r'L_\1', r'R_\1'),
    # prefix: Left_ / Right_
    (re.compile(r'^Left_(.+)$', re.IGNORECASE), r'Right_\1', r'Left_\1'),
    (re.compile(r'^Right_(.+)$', re.IGNORECASE), r'Left_\1', r'Right_\1'),
]


def find_mirror_name(name, vg_names):
    """頂点グループ名から左右ミラーの対応名を検索する"""
    for pattern, replace_to, _replace_from in MIRROR_PATTERNS:
        m = pattern.match(name)
        if m:
            mirror = pattern.sub(replace_to, name)
            # 大文字小文字を考慮してマッチ
            for vg in vg_names:
                if vg.lower() == mirror.lower():
                    return name, vg
    return None, None


# ──────────────────────────────────────────────
#  オペレーター
# ──────────────────────────────────────────────

class BWT_OT_transfer_weights(bpy.types.Operator):
    """ウェイト転送を実行（確認ダイアログ付き）"""
    bl_idname = "bwt.transfer_weights"
    bl_label = "ウェイト転送を実行しますか？"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        """確認ダイアログを表示"""
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context):
        obj = context.active_object
        settings = context.scene.bwt_settings

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "メッシュオブジェクトが選択されていません")
            return {'CANCELLED'}

        count = settings.pair_count
        mode = settings.transfer_mode
        success_count = 0
        skip_count = 0

        for i in range(count):
            src = getattr(obj, f"bwt_src_{i}", "")
            dst = getattr(obj, f"bwt_dst_{i}", "")

            if src and dst:
                mod = obj.modifiers.new(name="BWT_Temp", type='VERTEX_WEIGHT_MIX')
                mod.mix_mode = mode  # 'SET' or 'ADD'
                mod.mix_set = "B"
                mod.vertex_group_a = dst  # コピー先
                mod.vertex_group_b = src  # コピー元
                bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
                success_count += 1
            else:
                skip_count += 1

        # 結果レポート
        if success_count > 0:
            mode_label = "上書き" if mode == 'SET' else "加算"
            self.report({'INFO'}, f"{success_count}組のウェイトを転送しました（{mode_label}モード）")
        if skip_count > 0:
            self.report({'WARNING'}, f"{skip_count}組は未設定のためスキップしました")

        return {'FINISHED'}


class BWT_OT_swap_pair(bpy.types.Operator):
    """元と先を入れ替える"""
    bl_idname = "bwt.swap_pair"
    bl_label = "元と先を入れ替え"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty()

    def execute(self, context: Context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}

        src_attr = f"bwt_src_{self.index}"
        dst_attr = f"bwt_dst_{self.index}"

        src_val = getattr(obj, src_attr, "")
        dst_val = getattr(obj, dst_attr, "")

        setattr(obj, src_attr, dst_val)
        setattr(obj, dst_attr, src_val)

        return {'FINISHED'}


class BWT_OT_clear_fields(bpy.types.Operator):
    """すべての選択フィールドをリセット"""
    bl_idname = "bwt.clear_fields"
    bl_label = "選択をリセット"
    bl_options = {'INTERNAL'}

    def execute(self, context: Context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}

        count = context.scene.bwt_settings.pair_count
        for i in range(count):
            setattr(obj, f"bwt_src_{i}", "")
            setattr(obj, f"bwt_dst_{i}", "")

        self.report({'INFO'}, "選択フィールドをリセットしました")
        return {'FINISHED'}


class BWT_OT_delete_all_vertex_groups(bpy.types.Operator):
    """すべての頂点グループを削除（確認ダイアログ付き）"""
    bl_idname = "bwt.delete_all_vertex_groups"
    bl_label = "全頂点グループを削除しますか？（元に戻せません）"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context):
        obj = context.active_object
        if obj and obj.vertex_groups:
            obj.vertex_groups.clear()
            self.report({'INFO'}, "すべての頂点グループを削除しました")
        else:
            self.report({'INFO'}, "頂点グループが存在しません")
        return {'FINISHED'}


class BWT_OT_auto_mirror(bpy.types.Operator):
    """左右ミラーの命名規則（.L/.R, _L/_R 等）から対応ペアを自動検出"""
    bl_idname = "bwt.auto_mirror"
    bl_label = "左右ミラーを自動検出"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context):
        obj = context.active_object
        settings = context.scene.bwt_settings

        if not obj or obj.type != 'MESH' or not obj.vertex_groups:
            self.report({'ERROR'}, "メッシュオブジェクトまたは頂点グループがありません")
            return {'CANCELLED'}

        vg_names = [vg.name for vg in obj.vertex_groups]
        found_pairs = []
        used = set()

        for name in vg_names:
            if name in used:
                continue
            src, dst = find_mirror_name(name, vg_names)
            if src and dst and src != dst and dst not in used:
                found_pairs.append((src, dst))
                used.add(src)
                used.add(dst)

        if not found_pairs:
            self.report({'WARNING'},
                        "ミラーペアが見つかりませんでした "
                        "（対応する命名規則: .L/.R, _L/_R, _left/_right 等）")
            return {'CANCELLED'}

        # ペア数を検出結果に合わせて更新（上限内で）
        pair_count = min(len(found_pairs), MAX_VERTEX_GROUP_PAIRS)
        settings.pair_count = pair_count

        for i in range(pair_count):
            src, dst = found_pairs[i]
            setattr(obj, f"bwt_src_{i}", src)
            setattr(obj, f"bwt_dst_{i}", dst)

        self.report({'INFO'}, f"{pair_count}組のミラーペアを検出しました")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  プロパティグループ
# ──────────────────────────────────────────────

class BWT_Settings(bpy.types.PropertyGroup):
    pair_count: bpy.props.IntProperty(
        name="ペア数",
        description="転送するボーンペアの数",
        default=1,
        min=1,
        max=MAX_VERTEX_GROUP_PAIRS,
    )
    transfer_mode: bpy.props.EnumProperty(
        name="転送モード",
        description="ウェイトの転送方法を選択",
        items=[
            ('SET', "上書き", "コピー先のウェイトを元のウェイトで完全に置き換えます"),
            ('ADD', "加算", "コピー先の既存ウェイトに元のウェイトを加算します"),
        ],
        default='SET',
    )


# ──────────────────────────────────────────────
#  パネル
# ──────────────────────────────────────────────

class BWT_PT_main_panel(bpy.types.Panel):
    """メインパネル"""
    bl_label = "Bone ウェイト転送"
    bl_idname = "BWT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ウェイト転送"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj or obj.type != 'MESH':
            box = layout.box()
            col = box.column(align=True)
            col.label(text="メッシュオブジェクトを", icon='ERROR')
            col.label(text="選択してください")
            return

        # オブジェクト情報の表示
        info_row = layout.row()
        info_row.label(text=f"{obj.name}", icon='OUTLINER_OB_MESH')
        vg_count = len(obj.vertex_groups)
        info_row.label(text=f"頂点グループ: {vg_count}")


class BWT_PT_settings_panel(bpy.types.Panel):
    """設定サブパネル"""
    bl_label = "設定"
    bl_idname = "BWT_PT_settings_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ウェイト転送"
    bl_parent_id = "BWT_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bwt_settings

        col = layout.column(align=True)
        col.prop(settings, "pair_count", text="ペア数")

        col.separator(factor=0.5)

        # 転送モード（ラジオボタン風）
        col.label(text="転送モード:")
        row = col.row(align=True)
        row.prop_enum(settings, "transfer_mode", 'SET')
        row.prop_enum(settings, "transfer_mode", 'ADD')


class BWT_PT_pairs_panel(bpy.types.Panel):
    """ペア設定サブパネル"""
    bl_label = "ペア設定"
    bl_idname = "BWT_PT_pairs_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ウェイト転送"
    bl_parent_id = "BWT_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        settings = context.scene.bwt_settings

        if not obj or obj.type != 'MESH':
            return

        # 自動検出ボタン
        auto_row = layout.row()
        auto_row.scale_y = 1.2
        auto_row.operator("bwt.auto_mirror", text="左右ミラー自動検出", icon='MOD_MIRROR')

        layout.separator(factor=0.3)

        # 各ペアの表示
        count = settings.pair_count
        for i in range(count):
            pair_box = layout.box()

            # ペア番号ヘッダー
            header = pair_box.row()
            header.label(text=f"ペア {i + 1}", icon='BONE_DATA')

            # 元（コピー元）
            pair_box.prop_search(
                obj, f"bwt_src_{i}",
                obj, "vertex_groups",
                text="元",
                icon='FORWARD',
            )

            # スワップボタン（中央配置）
            swap_row = pair_box.row()
            swap_row.alignment = 'CENTER'
            op = swap_row.operator("bwt.swap_pair", text="入れ替え", icon='FILE_REFRESH')
            op.index = i

            # 先（コピー先）
            pair_box.prop_search(
                obj, f"bwt_dst_{i}",
                obj, "vertex_groups",
                text="先",
                icon='BACK',
            )


class BWT_PT_actions_panel(bpy.types.Panel):
    """実行サブパネル"""
    bl_label = "実行"
    bl_idname = "BWT_PT_actions_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ウェイト転送"
    bl_parent_id = "BWT_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bwt_settings

        # 転送実行ボタン（大きく目立たせる）
        run_row = layout.row()
        run_row.scale_y = 1.8
        mode_label = "上書き" if settings.transfer_mode == 'SET' else "加算"
        run_row.operator(
            "bwt.transfer_weights",
            text=f"ウェイト転送（{mode_label}）",
            icon='MOD_VERTEX_WEIGHT',
        )

        layout.separator(factor=0.5)

        # クリア系ボタン
        col = layout.column(align=True)
        col.operator("bwt.clear_fields", text="選択フィールドをリセット", icon='LOOP_BACK')

        layout.separator(factor=0.3)

        # 削除ボタン（危険操作なので分離）
        danger_row = layout.row()
        danger_row.alert = True
        danger_row.operator(
            "bwt.delete_all_vertex_groups",
            text="全頂点グループを削除",
            icon='TRASH',
        )


# ──────────────────────────────────────────────
#  登録 / 解除
# ──────────────────────────────────────────────

classes = (
    BWT_Settings,
    BWT_OT_transfer_weights,
    BWT_OT_swap_pair,
    BWT_OT_clear_fields,
    BWT_OT_delete_all_vertex_groups,
    BWT_OT_auto_mirror,
    BWT_PT_main_panel,
    BWT_PT_settings_panel,
    BWT_PT_pairs_panel,
    BWT_PT_actions_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.bwt_settings = bpy.props.PointerProperty(type=BWT_Settings)

    # ペア用プロパティを上限分まとめて登録
    for i in range(MAX_VERTEX_GROUP_PAIRS):
        setattr(
            bpy.types.Object,
            f"bwt_src_{i}",
            bpy.props.StringProperty(
                name=f"元 {i + 1}",
                description="コピー元の頂点グループ",
            ),
        )
        setattr(
            bpy.types.Object,
            f"bwt_dst_{i}",
            bpy.props.StringProperty(
                name=f"先 {i + 1}",
                description="コピー先の頂点グループ",
            ),
        )


def unregister():
    for i in range(MAX_VERTEX_GROUP_PAIRS):
        try:
            delattr(bpy.types.Object, f"bwt_src_{i}")
            delattr(bpy.types.Object, f"bwt_dst_{i}")
        except AttributeError:
            pass

    del bpy.types.Scene.bwt_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
