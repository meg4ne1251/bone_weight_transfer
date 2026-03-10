import bpy

# アクティブなオブジェクトを取得
obj = bpy.context.active_object

# オブジェクトが選択されているか確認
if obj and obj.type == 'MESH':
    # Vertex Weight Mixモディファイアを追加
    mod = obj.modifiers.new(name="頂点ウェイト合成", type='VERTEX_WEIGHT_MIX')
    
    # 必要に応じてモディファイアの設定を変更
    mod.mix_mode = 'ADD'  # ウェイトの合成方法
    mod.vertex_group_a = "a"  # グループAの名前　コピー先
    mod.vertex_group_b = "b"  # グループBの名前 コピー元
    mod.mix_set = "B"         # 頂点セットを頂点グループBにする。AならA　AとBならall
    
    print("頂点ウェイト合成モディファイアーが追加されました。")
else:
    print("メッシュオブジェクトが選択されていません。")