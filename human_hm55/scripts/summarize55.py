"""HM55 QA tables (Markdown) generated from $HM_BUILD/qa/*.json - no hand-copied numbers. Writes qa/QA_TABLES55.md."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hm_common as hc

Q = hc.BUILD/'qa'; J = lambda n: json.loads((Q/n).read_text()) if (Q/n).exists() else None
b = J('build_hm55.json'); v = J('verify_hm55.json'); pa = J('provenance_audit.json'); gv = J('gltf_validator.json'); wr = J('webtest55_result.json'); wa = J('webtest55_analysis.json')
L = ['# HM55 QA 表（スクリプト出力の実測値）\n']
L.append('## 1. 構成（書き出した GLB の実測）\n')
L.append('| GLB | 三角形 | 属性頂点 | プリミティブ | 画像 | 骨 | 動作 |'); L.append('|---|---|---|---|---|---|---|')
for n, s in sorted(v['structure'].items()):
    L.append(f"| {n} | {s['triangles']} | {s['attribute_vertices']} | {s['primitives']} | {s['images']} | {s['skins'][0]['joints'] if s['skins'] else 0} | {len(s['animations'])} |")
s0 = next(iter(v['structure'].values()))
L.append('\n### 材質（代表 1 体）\n'); L.append('| 材質 | alphaMode | 両面 |'); L.append('|---|---|---|')
for m in s0['materials']:
    L.append(f"| {m['name']} | {m['alphaMode']} | {m['doubleSided']} |")
L.append('\n### 動作クリップ\n'); L.append('| 名前 | 秒 | キー数 |'); L.append('|---|---|---|')
for a in s0['animations']:
    L.append(f"| {a['name']} | {a['seconds']} | {a['keys']} |")
L.append('\n### モジュール別の三角形数（生成時）\n'); L.append('| 部品 | 三角形 | 頂点 |'); L.append('|---|---|---|')
L.append(f"| 胴体（ユニフォーム＋腕脚の肌） | {b['body']['triangles']} | {b['body']['vertices_before_weld']} |")
for f, r in b['faces'].items():
    L.append(f"| 頭 {f} {r['name']}（顔・首・耳） | {r['triangles']} | {r['vertices']} |")
for k, r in b['hairs'].items():
    if k.startswith('P0_'):
        L.append(f"| 髪 {r['hair_id']}（P0 用） | {r['triangles']}（cap {r['cap_triangles']}、うち縁の帯 {r['edge_triangles']}、毛束 {r['card_triangles']}） | {r['vertices']} |")
L.append('\n## 2. 首と襟（優先①）：全動作・全コマの実測\n')
L.append('測定: 書き出した GLB を読み直し、各コマで姿勢を付けた頂点から計算。襟の隙間 = 襟の輪の各頂点から首の表面までの最短距離。'
         '首×シャツ = 頭部メッシュと上半身のシャツの三角形交差の対の数。見通し = 襟の隙間の中央を斜め上 3 方向から通した光線が、9cm 以内で肌に当たらなかった本数。\n')
L.append('| 選手 | 動作 | コマ | 胸に対する頭の回転 最大° | 襟の隙間 最小〜最大 mm | 首×シャツ 交差 最大 | 見通し 失敗/本数 |'); L.append('|---|---|---|---|---|---|---|')
for g, r in v['motion'].items():
    c = g.split('PLAYER_')[1].replace('_KITA.glb', '')
    L.append(f"| {c} | 静止 | — | 0 | {r['rest']['gap_min_mm']}〜{r['rest']['gap_max_mm']} | {r['rest']['neck_shirt_intersections']} | {r['rest']['see_through_misses']}/{r['rest']['see_through_rays']} |")
    for a, x in r['actions'].items():
        L.append(f"| {c} | {a} | {x['frames'][0]}〜{x['frames'][1]} | {x['head_vs_chest_deg_max']} | {x['gap_min_mm']}〜{x['gap_max_mm']} | {x['neck_shirt_intersections_max']} | {x['see_through_misses_max']}/{x['see_through_rays']} |")
L.append('\n### スキンの伸縮と、肌と布の交差（代表 1 体）\n')
L.append('辺の伸縮 = 姿勢を付けた辺の長さ ÷ 静止時の長さ。肌×布 = 肌の三角形とユニフォームの三角形の交差の対の数（静止時は 0）。\n')
L.append('| 動作 | 胴体の辺 最大 / 上位1% | 頭部の辺 最小 / 下位1% / 上位1% / 最大 | 肌×布 最大（コマ） | 最大コマでの内訳 |'); L.append('|---|---|---|---|---|')
r = next(iter(v['motion'].values()))
for a, x in r['actions'].items():
    L.append(f"| {a} | {x['stretch_body_max']} / {x['stretch_body_p99_max']} | {x['stretch_head_min']} / {x['stretch_head_p01_min']} / {x['stretch_head_p99_max']} / {x['stretch_head_max']} | {x['skin_cloth_intersections_max']}（{x['skin_cloth_worst_frame']}） | {x['skin_cloth_kinds_at_worst_frame']} |")
L.append('\n| メッシュ | 頂点 | ウェイト合計 最小〜最大 | 1頂点あたりの骨 最大 |'); L.append('|---|---|---|---|')
for n, w in r['weights'].items():
    L.append(f"| {n} | {w['vertices']} | {w['weight_sum_min']}〜{w['weight_sum_max']} | {w['max_influences']} |")
L.append('\n## 3. 肌色（優先②）：最終テクスチャの平均色\n')
L.append('頭部モジュールに首が含まれるため、頭と胴体のあいだに肌どうしの継ぎ目はありません。下は離れた部位どうしの色の差です（sRGB 0〜1、ΔE は CIE76）。\n')
L.append('| 顔 | 肌の色調 | 首 | 頬 | 前腕 | 膝 | ΔE 首−頬 | ΔE 首−前腕 | ΔE 首−膝 | 首の後ろの UV 継ぎ目の色差 |'); L.append('|---|---|---|---|---|---|---|---|---|---|')
for f, x in v['skin_colour'].items():
    m = x['mean_srgb']; d = x['deltaE76']; seam = b['skin_colour'].get('head_' + f, {}).get('back_seam_step_rgb_mean')
    L.append(f"| {f} | {x['tone']} | {m['neck']} | {m['cheek']} | {m['forearm']} | {m['knee']} | {d['neck_vs_cheek']} | {d['neck_vs_forearm']} | {d['neck_vs_knee']} | {seam} |")
L.append('\n陰影を焼き込む前の塗りの平均色（同じ色定義から作っていることの確認）:\n'); L.append('| 対象 | 平均 sRGB |'); L.append('|---|---|')
for k, x in b['skin_colour'].items():
    L.append(f"| {k} | {x.get('painted_mean_rgb') or x.get('neck_painted_mean_rgb')} |")
L.append('\n## 4. 髪と耳（優先③）：16 組の実測\n')
L.append('縁の高さ = 頭皮層（cap＋生え際の帯）の外周の頂点が、頭の表面（耳を除く）から浮いている高さ。耳の近く = 方位 58〜102°。\n')
L.append('| 組 | 髪の三角形 | 髪×頭 交差 | 縁の頂点 | 縁の高さ 最小/中央/最大 mm | 耳の近くの縁 中央/最大 mm | 髪と耳の最短距離 mm |'); L.append('|---|---|---|---|---|---|---|')
for g, h in v['hair'].items():
    c = g.split('PLAYER_')[1].replace('_KITA.glb', ''); e = h['hairline_edge_height_mm']; n = h['hairline_edge_height_near_ears_mm']
    L.append(f"| {c} | {h['hair_triangles']} | {h['hair_vs_head_intersections']} | {h['hairline_edge_vertices']} | {e['min']}/{e['median']}/{e['max']} | {n['median']}/{n['max']} | {h['hair_to_ear_min_distance_mm']} |")
if pa:
    L.append('\n## 5. 出自の監査\n')
    d = pa['derivation_of_earlier_work']; x = d['FACE52_face_vs_Reference04_mesh']
    L.append(f"- FACE52 の顔の頂点 {x['of']} 個のうち、引継ぎ資料の平行移動を掛けると Reference04 の頂点と一致するもの: **{x['coincident']} 個**")
    L.append('\n| 以前の成果物 | FACE52 と同じ面構成 | FACE52 と同じ UV | 動かしていない頂点 | テクスチャと FACE52 の相関（最大） |'); L.append('|---|---|---|---|---|')
    for k, r_ in d.items():
        if 'same_polygon_list_as_FACE52' in r_:
            tc = max((t['correlation'] for t in r_['texture_correlation_with_FACE52'].values()), default=None)
            L.append(f"| {k} | {r_['same_polygon_list_as_FACE52']} | {r_['same_uv_as_FACE52']} | {r_['vertices_unmoved_lt_0.1mm']} / {r_['vertices']} | {tc} |")
    L.append('\n| HM55 のメッシュ | 頂点 | 三角形 | 研究用メッシュと同じ頂点数・三角形数 | 一致する頂点（Reference04 / FACE52 / FH54 の最大） |'); L.append('|---|---|---|---|---|')
    for n, r_ in pa['hm55_vs_research']['meshes'].items():
        mx = max(val for key, val in r_.items() if key.startswith('coincident_vertices_with_'))
        L.append(f"| {n} | {r_['vertices']} | {r_['triangles']} | {r_['same_vertex_and_triangle_count_as_any_research_mesh']} | {r_['coincident_vertices_with_Reference04']} / {r_['coincident_vertices_with_FACE52']} / {mx} |")
    L.append('\n| HM55 のテクスチャ | 大きさ | 最も似た研究用画像 | 相関 |'); L.append('|---|---|---|---|')
    for n, t in pa['hm55_vs_research']['textures'].items():
        L.append(f"| {n} | {t['size'][0]}x{t['size'][1]} | {t['most_similar_research_image']} | {t['correlation']} |")
    sk = pa['hm55_vs_research']['skeleton']
    L.append(f"\n- 骨: HM55 {sk['hm55_bones']} 本、Reference04 {sk['reference04_bones']} 本。同じ名前の骨 {len(sk['shared_bone_names'])}、関節位置が 1mm 以内で一致するもの {sk['hm55_joint_positions_coinciding_with_reference_joints_lt_1mm']}。")
    L.append(f"- 動作: HM55 = {pa['hm55_vs_research']['actions']['hm55']}、Reference04 = {pa['hm55_vs_research']['actions']['reference04']}")
    n_reads = sum(len(x) for x in pa['hm55_build_inputs']['file_reads_in_build_scripts'].values())
    L.append(f"- 生成スクリプト内のファイル読み込み箇所: {n_reads} か所（すべて同じビルドで書き出したテクスチャの読み戻しと SHA 計算。一覧は provenance_audit.json）")
if gv:
    L.append('\n## 6. glTF Validator（Khronos 公式 ' + list(gv.values())[0]['validatorVersion'] + '）\n')
    L.append(f"- 対象 {len(gv)} ファイル、エラー {sum(x['errors'] for x in gv.values())}、警告 {sum(x['warnings'] for x in gv.values())}、情報 {sum(x['infos'] for x in gv.values())}")
    msgs = sorted({m for x in gv.values() for m in x['messages']})
    for m in msgs[:12]:
        L.append(f'  - {m}')
if wr:
    L.append(f"\n## 7. ブラウザ（three.js {wr['three']}、ヘッドレス Chromium + SwiftShader ソフトウェア描画）\n")
    L.append('| モデル | スキン付きメッシュ | 骨 | クリップ | 描画順を最悪にしたときの変化画素% [斜め, 上, 背面, 側面] | 裏面を描かない設定での変化画素% |'); L.append('|---|---|---|---|---|---|')
    for m, x in wr['models'].items():
        a = (wa or {}).get(m, {})
        L.append(f"| {m} | {x['skinned']} | {x['bones']} | {len(x['clips'])} | {list(a.get('order_changed_pixels_pct', {}).values())} | {a.get('front_only_vs_double_sided_changed_pixels_pct')} |")
    L.append('\n| 22 体表示 | 描画コール | 三角形 | ms/コマ（SwiftShader、参考値） |'); L.append('|---|---|---|---|')
    for k, p in wr['perf'].items():
        L.append(f"| {k} | {p['calls']} | {p['triangles']} | {p['ms_per_frame']:.2f} |")
    L.append(f"\n- ページのエラー: {len(wr['page_errors'])} 件")
(Q/'QA_TABLES55.md').write_text('\n'.join(L) + '\n'); print('ok', len(L))
