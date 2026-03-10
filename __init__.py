import bpy
from bpy.types import Context

# プロパティの最大数（register時に一括登録）
MAX_VERTEX_GROUP_PAIRS = 20

# 左右ミラー検出用のパターン定義 (左側サフィックス/プレフィックス, 右側)
MIRROR_SUFFIX_PAIRS = [
    ('.L', '.R'),
    ('_L', '_R'),
    ('_left', '_right'),
    ('.left', '.right'),
]

MIRROR_PREFIX_PAIRS = [
    ('L_', 'R_'),
    ('Left_', 'Right_'),
]


def _match_case(source, target):
    """sourceの大文字小文字パターンをtargetに適用する"""
    if source.isupper():
        return target.upper()
    if source.islower():
        return target.lower()
    # 先頭だけ大文字などの混合パターン: 文字単位でマッピング
    result = []
    for i, ch in enumerate(target):
        if i < len(source):
            result.append(ch.upper() if source[i].isupper() else ch.lower())
        else:
            result.append(ch)
    return ''.join(result)


def find_mirror_name(name, vg_names):
    """頂点グループ名から左右ミラーの対応名を検索する"""
    name_lower = name.lower()
    candidate = None

    # サフィックスパターンのチェック
    for left, right in MIRROR_SUFFIX_PAIRS:
        if name_lower.endswith(left.lower()):
            # 元の名前から実際のサフィックス部分を取得し、大文字小文字を保持して置換
            original_suffix = name[len(name) - len(left):]
            replacement = _match_case(original_suffix, right)
            candidate = name[:len(name) - len(left)] + replacement
            break
        if name_lower.endswith(right.lower()):
            original_suffix = name[len(name) - len(right):]
            replacement = _match_case(original_suffix, left)
            candidate = name[:len(name) - len(right)] + replacement
            break

    # プレフィックスパターンのチェック
    if candidate is None:
        for left, right in MIRROR_PREFIX_PAIRS:
            if name_lower.startswith(left.lower()):
                original_prefix = name[:len(left)]
                replacement = _match_case(original_prefix, right)
                candidate = replacement + name[len(left):]
                break
            if name_lower.startswith(right.lower()):
                original_prefix = name[:len(right)]
                replacement = _match_case(original_prefix, left)
                candidate = replacement + name[len(right):]
                break

    if candidate:
        # 大文字小文字を無視して実際の頂点グループ名を検索
        for vg in vg_names:
            if vg.lower() == candidate.lower():
                return name, vg

    return None, None


def ensure_pairs(obj, count):
    """ペアコレクションがちょうど必要な数だけあることを保証する"""
    pairs = obj.bwt_pairs
    while len(pairs) < count:
        pairs.add()
    while len(pairs) > count:
        pairs.remove(len(pairs) - 1)


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
        ensure_pairs(obj, count)
        mode = settings.transfer_mode
        success_count = 0
        skip_count = 0
        error_count = 0

        for i in range(count):
            pair = obj.bwt_pairs[i]
            src = pair.src
            dst = pair.dst

            if src and dst:
                # 転送先の頂点グループが存在しない場合は作成
                if dst not in obj.vertex_groups:
                    obj.vertex_groups.new(name=dst)

                mod = obj.modifiers.new(name="BWT_Temp", type='VERTEX_WEIGHT_MIX')
                mod.mix_mode = mode  # 'SET' or 'ADD'
                mod.mix_set = "B"
                mod.mask_constant = 1.0  # 全頂点に対して転送を適用
                mod.vertex_group_a = dst  # コピー先
                mod.vertex_group_b = src  # コピー元
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
                    success_count += 1
                except RuntimeError as e:
                    obj.modifiers.remove(mod)
                    self.report({'ERROR'}, f"ペア {i + 1} の転送に失敗: {e}")
                    error_count += 1
            else:
                skip_count += 1

        # 結果レポート
        if success_count > 0:
            mode_label = "上書き" if mode == 'SET' else "加算"
            self.report({'INFO'}, f"{success_count}組のウェイトを転送しました（{mode_label}モード）")
        if skip_count > 0:
            self.report({'WARNING'}, f"{skip_count}組は未設定のためスキップしました")
        if error_count > 0:
            self.report({'ERROR'}, f"{error_count}組の転送に失敗しました")

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

        ensure_pairs(obj, self.index + 1)
        pair = obj.bwt_pairs[self.index]
        tmp = pair.src
        pair.src = pair.dst
        pair.dst = tmp

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
        ensure_pairs(obj, count)
        for i in range(count):
            pair = obj.bwt_pairs[i]
            pair.src = ""
            pair.dst = ""

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
        ensure_pairs(obj, pair_count)

        for i in range(pair_count):
            src, dst = found_pairs[i]
            pair = obj.bwt_pairs[i]
            pair.src = src
            pair.dst = dst

        self.report({'INFO'}, f"{pair_count}組のミラーペアを検出しました")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  プロパティグループ
# ──────────────────────────────────────────────

class BWT_PairItem(bpy.types.PropertyGroup):
    src: bpy.props.StringProperty(
        name="元",
        description="コピー元の頂点グループ",
    )
    dst: bpy.props.StringProperty(
        name="先",
        description="コピー先の頂点グループ",
    )


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
        obj = context.active_object

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
        obj = context.active_object
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
        ensure_pairs(obj, count)

        for i in range(count):
            pair = obj.bwt_pairs[i]
            pair_box = layout.box()

            # ペア番号ヘッダー
            header = pair_box.row()
            header.label(text=f"ペア {i + 1}", icon='BONE_DATA')

            # 元（コピー元）
            pair_box.prop_search(
                pair, "src",
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
                pair, "dst",
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
    BWT_PairItem,
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
    bpy.types.Object.bwt_pairs = bpy.props.CollectionProperty(type=BWT_PairItem)


def unregister():
    del bpy.types.Object.bwt_pairs
    del bpy.types.Scene.bwt_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
