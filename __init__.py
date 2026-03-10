import bpy
from bpy.types import Context

# プロパティの最大数（register時に一括登録）
MAX_VERTEX_GROUP_PAIRS = 20


MIRROR_SUFFIX_PAIRS = [('.L', '.R'), ('_L', '_R'), ('_left', '_right'), ('.left', '.right')]
MIRROR_PREFIX_PAIRS = [('L_', 'R_'), ('Left_', 'Right_')]


def flip_lr(name):
    """名前のL/Rを反転する。対応パターンがなければ空文字を返す"""
    nl = name.lower()
    for a, b in MIRROR_SUFFIX_PAIRS:
        if nl.endswith(a.lower()):
            return name[:-len(a)] + b
        if nl.endswith(b.lower()):
            return name[:-len(b)] + a
    for a, b in MIRROR_PREFIX_PAIRS:
        if nl.startswith(a.lower()):
            return b + name[len(a):]
        if nl.startswith(b.lower()):
            return a + name[len(b):]
    return ""


def ensure_pairs(obj, count):
    """ペアコレクションが count 以上あることを保証する（既存データは削除しない）"""
    pairs = obj.bwt_pairs
    while len(pairs) < count:
        pairs.add()


def _deferred_ensure_pairs(obj_name, count):
    """draw()の外でペアを初期化し、再描画をトリガーする"""
    obj = bpy.data.objects.get(obj_name)
    if obj and len(obj.bwt_pairs) < count:
        ensure_pairs(obj, count)
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
    return None  # タイマーを繰り返さない


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
        delete_source = settings.delete_source
        success_count = 0
        skip_count = 0
        error_count = 0
        transferred_srcs = []

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
                    transferred_srcs.append(src)
                except RuntimeError as e:
                    obj.modifiers.remove(mod)
                    self.report({'ERROR'}, f"ペア {i + 1} の転送に失敗: {e}")
                    error_count += 1
            else:
                skip_count += 1

        # 転送元の削除
        if delete_source and transferred_srcs:
            for src_name in transferred_srcs:
                vg = obj.vertex_groups.get(src_name)
                if vg:
                    obj.vertex_groups.remove(vg)

        # 結果レポート
        if success_count > 0:
            mode_label = "上書き" if mode == 'SET' else "加算"
            delete_label = "（転送元を削除）" if delete_source else ""
            self.report({'INFO'}, f"{success_count}組のウェイトを転送しました（{mode_label}モード）{delete_label}")
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


class BWT_OT_add_mirror_pair(bpy.types.Operator):
    """元と先の名前をL/R反転した新しいペアを追加する"""
    bl_idname = "bwt.add_mirror_pair"
    bl_label = "LR反転ペアを追加"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context: Context):
        obj = context.active_object
        settings = context.scene.bwt_settings

        ensure_pairs(obj, self.index + 1)
        pair = obj.bwt_pairs[self.index]

        if not pair.src and not pair.dst:
            self.report({'WARNING'}, "元と先が未設定です")
            return {'CANCELLED'}

        new_src = flip_lr(pair.src) if pair.src else ""
        new_dst = flip_lr(pair.dst) if pair.dst else ""

        if not new_src and not new_dst:
            self.report({'WARNING'}, "L/Rパターンが見つかりませんでした（.L/.R, _L/_R 等が必要です）")
            return {'CANCELLED'}

        # 次の空きスロットを探す、なければ末尾に追加
        count = settings.pair_count
        ensure_pairs(obj, count)
        new_index = next(
            (i for i in range(count) if not obj.bwt_pairs[i].src and not obj.bwt_pairs[i].dst),
            None,
        )
        if new_index is None:
            if count >= MAX_VERTEX_GROUP_PAIRS:
                self.report({'WARNING'}, f"ペアが上限（{MAX_VERTEX_GROUP_PAIRS}）に達しています")
                return {'CANCELLED'}
            new_index = count
            settings.pair_count = count + 1
            ensure_pairs(obj, count + 1)

        new_pair = obj.bwt_pairs[new_index]
        new_pair.src = new_src
        new_pair.dst = new_dst

        self.report({'INFO'}, f"LR反転ペアをペア {new_index + 1} に追加しました")
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
    delete_source: bpy.props.BoolProperty(
        name="転送後に転送元を削除",
        description="転送完了後、転送元の頂点グループを削除します",
        default=False,
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

        col.separator(factor=0.5)
        col.prop(settings, "delete_source")


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

        # 各ペアの表示
        count = settings.pair_count

        # draw()内でのデータ変更は禁止されているため、不足時はタイマーで遅延初期化
        if len(obj.bwt_pairs) < count:
            bpy.app.timers.register(
                lambda: _deferred_ensure_pairs(obj.name, count),
                first_interval=0.0,
            )
            return

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

            # 操作ボタン（中央配置）
            btn_row = pair_box.row(align=True)
            btn_row.alignment = 'CENTER'
            op = btn_row.operator("bwt.swap_pair", text="入れ替え", icon='FILE_REFRESH')
            op.index = i
            op = btn_row.operator("bwt.add_mirror_pair", text="LR反転追加", icon='MOD_MIRROR')
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
    BWT_OT_add_mirror_pair,
    BWT_OT_clear_fields,
    BWT_OT_delete_all_vertex_groups,
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
