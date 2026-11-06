"""FH54 QA tables (Markdown) generated from build/qa/*.json - no hand-copied numbers. Writes build/qa/QA_TABLES54.md."""
import sys, json, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fh53_common as fc

Q = fc.BUILD/'qa'; W = fc.BUILD/'webtest'
for src in (W/'out/webtest_result.json', W/'out/webtest_analysis.json', W/'sweep/flip_analysis.json', W/'sweep/sweep_orders.json', W/'force/force_order_result.json'):
    if src.exists():
        shutil.copy2(src, Q/('webtest_' + src.name if not src.name.startswith('webtest') else src.name))
J = lambda n: json.loads((Q/n).read_text())
v = J('verify_all.json'); hb = J('build_hairs_H1_H2_H3_H4.json'); fb = J('build_faces54.json'); qf = J('qa_faces54.json')
fd = J('face_distinct54.json'); an = J('anim_ref04.json'); gv = J('gltf_validator.json')
L = ['# FH54 QA 表（スクリプト出力の実測値）\n']
L.append('## 1. 顔×髪 20組の交差・貫通・隙間・透過（GLB実測）\n')
L.append('判定方法: 交差 = GLBプリミティブ同士のBVH三角形交差（epsilon 0、髪同士は頂点位置を共有するだけの接触を除外）。'
         '皮膚の突出 = 皮膚33,120点の放射方向判定。生え際の縁の高さ = cap縁（頂点alpha≤0.1）の皮膚からの高さ。'
         '頭蓋開口上の半透明 = 皮膚の無い方向で alpha<0.99 の cap 頂点。\n')
L.append('| 区分 | 組 | 髪×皮膚 | cap×カード | カード同士 | capの外の皮膚点 | 最小capすき間 mm | 縁の高さ中央値 mm | 開口上の半透明頂点 |')
L.append('|---|---|---|---|---|---|---|---|---|')
for k, r in [('FACE52 原本GLB', v['FACE52_final_baseline'])] + list(v['combos'].items()):
    grp = 'H0原本（対照）' if (k.endswith('_H0') or k.startswith('FACE52')) else '新髪H1〜H4'
    c = r['contacts']; h = r['hair']; he = h['hairline_edge_height_mm']
    hem = f"{he['median']:.2f}" if he and he['median'] == he['median'] else '—'
    L.append(f"| {grp} | {k} | {c['hair_vs_skin_total']} | {c['hair_cap_vs_cards']} | {sum(c['hair_self_nonshared'].values())} | {h['skin_points_outside_cap']} | {h['min_cap_clearance_mm']:.2f} | {hem} | {h['cap_vertices_alpha_lt_0.99_over_open_skull']} |")
L.append('\n### カードの接触の内訳（F0の各髪。根元フェード帯 = テクスチャalphaが0付近の根元22%）\n')
L.append('| 組 | 相手 | 対 | カード三角形 | うち根元フェード帯 | 根元より先 |')
L.append('|---|---|---|---|---|---|')
for k in ('F0_H1', 'F0_H2', 'F0_H3', 'F0_H4'):
    cc = v['combos'][k].get('card_contacts', {})
    for pair, r in cc.items():
        L.append(f"| {k} | {pair.split(' | ')[1]} | {r['pairs']} | {r['card_triangles']} | {r['card_triangles_in_root_fade']} | {r['card_triangles_beyond_root']} |")
L.append('\n## 2. 計測値（三角形・属性頂点・材質・テクスチャ）\n')
L.append('| GLB | 三角形 | 属性頂点 | プリミティブ | 材質 | テクスチャ | 解像度 |')
L.append('|---|---|---|---|---|---|---|')
for name, st in [('TM_FACE52_F0_H0.glb（原本）', v['metrics']['FACE52_final'])] + sorted((k, s) for k, s in v['metrics'].items() if k != 'FACE52_final'):
    res = ', '.join('%sx%s' % (i['w'], i['h']) for i in st['images'])
    L.append(f"| {name} | {st['triangles']} | {st['attribute_vertices']} | {st['primitives']} | {st['materials']} | {len(st['images'])} | {res} |")
L.append('\n## 3. 髪の構築記録\n')
L.append('| 髪 | cap三角形 | カード | カード三角形 | cap押出(放射/交差) | カード押出 max/p95 mm（上限2.5） | 皮膚に当たり先端を切ったカード | 交差残（髪同士） |')
L.append('|---|---|---|---|---|---|---|---|')
for k, r in hb['hairs'].items():
    c = r['card_vs_skin_cap_and_layer_overlap_pass']
    L.append(f"| {r['hair_id']} | {r['cap_triangles']} | {r['cards']} | {r['card_triangles']} | {r['cap_radial_clearance_pass']['vertex_pushes']}/{r['cap_vs_skin_overlap_pass']['vertex_pushes']} | {c['card_vertex_push_mm']['max']}/{c['card_vertex_push_mm']['p95']} | {len(c['cards_trimmed_at_skin'])} | {c['remaining_overlapping_triangles']} |")
L.append('\n## 4. 顔の変形・UV・継ぎ目\n')
L.append('| 顔 | 皮膚の最大変位 mm | 耳の最大変位 mm | 首側開放縁 mm | 後頭皮共有頂点 mm | z>0.080皮膚 mm | 法線反転 | UV伸び 皮膚max | 皮膚±25%超 三角形 | 耳±25%超 三角形 | 皮膚継ぎ目の色段差 平均/最大 |')
L.append('|---|---|---|---|---|---|---|---|---|---|---|')
for f in ('F1', 'F2', 'F3'):
    b = fb['faces'][f'{f}_full']; u = qf[f]['uv_stretch_vs_FACE52']; s = qf[f]['material_seam_colour_step_sRGB']
    L.append(f"| {b['face_id']} | {b['max_skin_displacement_mm']} | {b['max_ear_displacement_mm']} | {b['neck_boundary_max_move_mm']} | {b['backscalp_shared_vertices_max_move_mm']} | {b['max_skin_move_above_z0.080_mm']} | {b['face_normal_flips']} | {u['skin']['stretch_max']} | {u['skin']['over_1.25x_or_under_0.8x']} | {u['ear']['over_1.25x_or_under_0.8x']} | {s['step_mean']}/{s['step_max']} |")
s0 = qf['F0']['material_seam_colour_step_sRGB']; L.append(f"| F0 原本 | — | — | — | — | — | — | — | — | — | {s0['step_mean']}/{s0['step_max']} |")
L.append('\n## 5. 小さい表示での顔の差（同じ髪H0・同じカメラ、顔4種の総当たり平均画素差 /255）\n')
L.append('| 条件 | FH53 平均 | FH53 最小の組 | FH54 平均 | FH54 最小の組 |')
L.append('|---|---|---|---|---|')
for px in (64, 128):
    for vw in ('front', 'quarter_R'):
        a = fd[f'FH53_{px}px_{vw}']; b = fd[f'FH54_{px}px_{vw}']
        L.append(f"| {px}px {vw} | {a['mean_pair_diff']} | {a['min_pair_diff']} | {b['mean_pair_diff']} | {b['min_pair_diff']} |")
L.append('\n## 6. Reference04 既存動作での首の接合（仮の固定接続 / 仮のウェイト転写）\n')
L.append('| 組・方式 | 静止時 隙間max mm | 動作 | 頭の首に対する回転max ° | 隙間max mm | 最大のフレーム |')
L.append('|---|---|---|---|---|---|')
for k, r in an['runs'].items():
    for act, a in r['actions'].items():
        L.append(f"| {k} | {r['rest_gap_mm']['max']:.2f} | {act} | {a['head_rot_vs_neck_deg_max']:.1f} | {a['gap_max_mm']:.2f} | {a['gap_max_frame']} |")
if (Q/'webtest_result.json').exists():
    wr = J('webtest_result.json'); fo = J('webtest_force_order_result.json') if (Q/'webtest_force_order_result.json').exists() else {}
    fl = J('webtest_flip_analysis.json') if (Q/'webtest_flip_analysis.json').exists() else {}
    L.append('\n## 7. ブラウザ（three.js 0.186.1、ヘッドレスChromium + SwiftShader ソフトウェア描画）\n')
    L.append('| モデル | 透過プリミティブ | 仰角スイープで描画順が入れ替わった回数 | 最悪順へ強制したときの変化画素% [斜め, 上, 背面] |')
    L.append('|---|---|---|---|')
    for m in fo:
        L.append(f"| {m} | {', '.join(fl.get(m, {}).get('transparent_primitives', []))} | {fl.get(m, {}).get('order_flips_in_sweep', '—')} | {fo[m]} |")
    L.append('\n| 22体表示 | 描画コール | 三角形 | ms/フレーム（SwiftShader、参考値） |')
    L.append('|---|---|---|---|')
    for k, p in wr['perf'].items():
        L.append(f"| {k} | {p['calls']} | {p['triangles']} | {p['ms_per_frame']:.2f} |")
L.append('\n## 8. glTF Validator（Khronos 公式 ' + list(gv.values())[0]['validatorVersion'] + '）\n')
L.append(f"- 対象 {len(gv)} ファイル、エラー {sum(x['errors'] for x in gv.values())}、警告 {sum(x['warnings'] for x in gv.values())}、情報 {sum(x['infos'] for x in gv.values())}")
L.append('\n## 9. .blend 開き直し・GLB 再読込\n')
L.append('| .blend | 開いた版 | 画像 | 欠落 | 読込不可 |')
L.append('|---|---|---|---|---|')
for k, r in v['blend_reopen'].items():
    L.append(f"| {k} | {r['opened_with']} | {len(r['images'])} | {r['missing_images']} | {r['unloadable_images']} |")
L.append('\n| GLB | 位置 max | 法線 max ° | UV max | 頂点色 max | 材質一致 |')
L.append('|---|---|---|---|---|---|')
for k, r in v['glb_roundtrip'].items():
    pm = r['compare']['per_material']
    if all(isinstance(x, dict) for x in pm.values()):
        L.append(f"| {k} | {max(x['pos_max_abs'] for x in pm.values()):.1e} | {max(x['normal_max_deg'] for x in pm.values()):.3f} | {max(x['uv_max_abs'] for x in pm.values()):.1e} | {max(x['colour_max_abs'] for x in pm.values()):.1e} | {r['compare']['materials_a'] == r['compare']['materials_b']} |")
    else:
        L.append(f'| {k} | NG | {pm} |')
(Q/'QA_TABLES54.md').write_text('\n'.join(L) + '\n'); print('ok', len(L))
