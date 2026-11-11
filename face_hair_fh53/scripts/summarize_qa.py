"""Build markdown tables from build/qa/*.json (no hand-copied numbers). Writes build/qa/QA_TABLES.md and qa/ copy."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fh53_common as fc

Q = fc.BUILD/'qa'
v = json.loads((Q/'verify_all.json').read_text())
hb = json.loads(next(Q.glob('build_hairs_H1_H2_H3_H4.json')).read_text())
fb = json.loads(next(Q.glob('build_faces_F1_F2_F3.json')).read_text())
L = []
m = v['metrics']; base = m['FACE52_final']
def img_s(st):
    return ', '.join(f"{i['w']}x{i['h']}" for i in st['images'])
L.append('## 計測値（GLB実測）\n')
L.append('| GLB | 三角形 | 属性頂点 | プリミティブ | 材質 | テクスチャ枚数 | テクスチャ解像度 | 三角形差 |')
L.append('|---|---|---|---|---|---|---|---|')
for name, st in [('TM_FACE52_F0_H0.glb (原本)', base)] + sorted((k, s) for k, s in m.items() if k != 'FACE52_final'):
    ref = 736 if '_F' in name and name.count('_') >= 3 and '_H' not in name else (2424 if name.startswith('TM_FH53_H') else base['triangles'])
    refname = {736: 'FACE52顔+後頭皮 736', 2424: 'FACE52髪 2424'}.get(ref, 'FACE52頭部 3160')
    L.append(f"| {name} | {st['triangles']} | {st['attribute_vertices']} | {st['primitives']} | {st['materials']} | {len(st['images'])} | {img_s(st)} | {st['triangles'] - ref:+d}（対{refname}） |")
L.append('\n## 顔候補の変形記録\n')
skin = json.loads((Q/'face_skin_displacement.json').read_text())
L.append('| 顔 | 皮膚(耳以外)の最大変位 mm | 耳の最大変位 mm | 首側開放縁の最大移動 mm | 後頭皮との共有頂点 最大移動 mm | z>0.080 皮膚の最大移動 mm | 面法線反転 | 面積比 最小/最大 |')
L.append('|---|---|---|---|---|---|---|---|')
for k, r in fb['faces'].items():
    L.append(f"| {r['face_id']} | {skin[k]} | {r['max_ear_displacement_mm']} | {r['neck_boundary_max_move_mm']} | {r['backscalp_shared_vertices_max_move_mm']} | {r['max_skin_move_above_z0.080_mm']} | {r['face_normal_flips']} | {r['min_area_ratio']} / {r['max_area_ratio']} |")
L.append('\n## 髪候補の構築記録\n')
L.append('| 髪 | cap三角形 | カード枚数 | カード三角形 | cap半径方向クリアランス押出 | cap×皮膚 交差解消 | カード×皮膚/cap 交差解消 | カード押出 max/p95 mm |')
L.append('|---|---|---|---|---|---|---|---|')
for k, r in hb['hairs'].items():
    c = r['card_vs_skin_cap_and_layer_overlap_pass']
    L.append(f"| {r['hair_id']} | {r['cap_triangles']} | {r['cards']} | {r['card_triangles']} | {r['cap_radial_clearance_pass']['vertex_pushes']}頂点, 残{r['cap_radial_clearance_pass']['remaining']} | 残{r['cap_vs_skin_overlap_pass']['remaining_overlapping_triangles']} | 残{c['remaining_overlapping_triangles']} | {c['card_vertex_push_mm']['max']} / {c['card_vertex_push_mm']['p95']} |")
L.append('\n## 顔×髪 組み合わせ検査（20通りすべて実施）\n')
L.append('BVH三角形交差は epsilon=0（FACE52 contact_compare46 と同方式）。皮膚突出は皮膚三角形を重心格子(n=8, 33,120点)で標本化し放射方向で判定。\n')
L.append('| 組み合わせ | 髪×皮膚 交差対 | cap×カード 交差対 | カード自己交差対(頂点非共有) | capより外の皮膚点 | 最小capクリアランス mm | 生え際縁の高さ 中央値 mm | 頭蓋開口上の半透明cap頂点 |')
L.append('|---|---|---|---|---|---|---|---|')
rows = [('FACE52原本 (TM_FACE52_F0_H0.glb)', v['FACE52_final_baseline'])] + [(k, r) for k, r in v['combos'].items()]
for k, r in rows:
    c = r['contacts']; h = r['hair']; selfc = sum(c['hair_self_nonshared'].values())
    he = h['hairline_edge_height_mm']; hem = f"{he['median']:.2f}" if he and he['median'] == he['median'] else '—'
    L.append(f"| {k} | {c['hair_vs_skin_total']} | {c['hair_cap_vs_cards']} | {selfc} | {h['skin_points_outside_cap']} | {h['min_cap_clearance_mm']:.2f} | {hem} | {h['cap_vertices_alpha_lt_0.99_over_open_skull']} |")
L.append('\n## GLB 再読込（空シーン）比較の最大差\n')
L.append('| GLB | 位置 max abs | 法線 max deg | 0.1度超の角 | UV max abs | 頂点色 max abs | 材質一致 |')
L.append('|---|---|---|---|---|---|---|')
for k, r in v['glb_roundtrip'].items():
    pm = r['compare']['per_material']; ok = all(isinstance(x, dict) for x in pm.values())
    if not ok:
        L.append(f'| {k} | NG {pm} |'); continue
    L.append(f"| {k} | {max(x['pos_max_abs'] for x in pm.values()):.2e} | {max(x['normal_max_deg'] for x in pm.values()):.3f} | {sum(x['normal_corners_over_0.1deg'] for x in pm.values())} | {max(x['uv_max_abs'] for x in pm.values()):.2e} | {max(x['colour_max_abs'] for x in pm.values()):.2e} | {r['compare']['materials_a'] == r['compare']['materials_b']} |")
L.append('\n## .blend 開き直し\n')
L.append('| .blend | 開いた版 | 保存版 | 画像数 | 欠落 | 読込不可 |')
L.append('|---|---|---|---|---|---|')
for k, r in v['blend_reopen'].items():
    L.append(f"| {k} | {r['opened_with']} | {'.'.join(map(str, r['file_saved_version']))} | {len(r['images'])} | {r['missing_images']} | {r['unloadable_images']} |")
L.append('\n## FACE52 原本 vs FH53 F0×H0 再書き出し（属性比較）\n')
for k, r in v['regression_F0_H0_vs_FACE52_final'].items():
    L.append(f'- {k}: ' + ', '.join(f'{a} {b}' for a, b in r.items()))
out = '\n'.join(L) + '\n'
(Q/'QA_TABLES.md').write_text(out)
print(out)
fc.finish()
