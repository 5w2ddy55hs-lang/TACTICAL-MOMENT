"""HM57 QA tables (Markdown) generated from $HM_BUILD/qa/*.json and the exported GLBs themselves - no hand-copied numbers.
  - size / triangles / texture bytes and resolutions per GLB (HM56, HM57, HM57 LITE)
  - where the triangles are: head triangles by region (face front, contour / ears, hairline, under the hair, neck, hidden
    in the shirt) and body triangles by part, read from the GLB vertex positions
  - skin weights read from JOINTS_0 / WEIGHTS_0 (sum, influences)
  - skeleton and clips compared byte for byte (HM56 vs HM57, HM57 vs LITE)
  - motion checks per clip (verify_motion57.json), glTF Validator, browser test, videos
Usage: HM_BUILD=... python summarize57.py <HM56 glb> <HM57 glb> <HM57 LITE glb>; writes qa/rig_identity57.json, qa/glb_breakdown57.json, qa/QA_TABLES57.md."""
import sys, io, json, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import hm_common as hc, glb_info, hm_lod as lod, hm_head as hh, hm_body as hb

G = {'HM56': Path(sys.argv[1]), 'HM57': Path(sys.argv[2]), 'HM57L': Path(sys.argv[3])}
NAME = {'HM56': 'HM56（改善前）', 'HM57': 'HM57（今回）', 'HM57L': 'HM57 軽量版'}
Q = hc.BUILD/'qa'; J = lambda n: json.loads((Q/n).read_text()) if (Q/n).exists() else None
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}; CT = {5126: ('f', 4), 5125: ('I', 4), 5123: ('H', 2), 5121: ('B', 1)}


def accessor(g, b, i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]; c, sz = CT[a['componentType']]; n = NC[a['type']]; off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', n*sz); out = np.zeros((a['count'], n))
    for k in range(a['count']):
        out[k] = struct.unpack_from('<%d%s' % (n, c), b, off + k*stride)
    if a.get('normalized'):
        out = out/{5121: 255.0, 5123: 65535.0}[a['componentType']]
    return out


def mesh_data(path):
    """World-space positions (glTF Y-up -> Blender Z-up), triangles, weights per primitive, with material name."""
    g, b = glb_info.read_glb(path); prims = []
    for m in g['meshes']:
        for p in m['primitives']:
            P = accessor(g, b, p['attributes']['POSITION']); P = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1); T = accessor(g, b, p['indices']).astype(int).reshape(-1, 3)
            W = accessor(g, b, p['attributes']['WEIGHTS_0']) if 'WEIGHTS_0' in p['attributes'] else None
            UV = accessor(g, b, p['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in p['attributes'] else None
            prims.append({'mesh': m['name'], 'material': g['materials'][p['material']]['name'], 'P': P, 'T': T, 'W': W, 'UV': UV})
    return g, b, prims


def images(g, b):
    from PIL import Image
    out = []
    for im in g.get('images', []):
        bv = g['bufferViews'][im['bufferView']]; data = b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]; pil = Image.open(io.BytesIO(data))
        out.append({'name': im.get('name'), 'mime': im.get('mimeType'), 'px': list(pil.size), 'bytes': bv['byteLength']})
    return out


HEAD_REGIONS = [('face', '顔の前面（目・鼻・口・顎）'), ('contour', '頬と顎の輪郭・耳'), ('hairline', '生え際'), ('scalp', '髪の下（見えない）'), ('neck', '首'), ('hidden', 'シャツの中（見えない）')]


def head_region(c):
    q = c - hb.HEAD_PIVOT; az, _, el = hh.azel_of(hh.P0, q[None]); az, el = float(az[0]), float(el[0]); line = float(hh.scalp_line_el(az)); z = q[2]
    if z < -0.135: return 'hidden'
    if z < -0.080: return 'neck'
    if el > line + 5.0: return 'scalp'
    if abs(el - line) < 5.0: return 'hairline'
    if az < 78: return 'face'
    return 'contour'


BODY_PARTS = [('shoulder', '肩・襟まわり（z>1.30）'), ('shirt', 'シャツの胴'), ('sleeve', '袖'), ('arm', '腕・手'), ('shorts', 'パンツ'), ('leg', '脚の肌'), ('sock', 'ソックス'), ('boot', 'スパイク'), ('other', 'その他')]


def body_part(c, uv, kit):
    """Part from the UV chart the triangle lies in (hm_body.KIT_RECT / SKIN_RECT; glTF v is flipped)."""
    u, v = uv[0], 1.0 - uv[1]
    for name, (u0, v0, u1, v1) in (hb.KIT_RECT if kit else hb.SKIN_RECT).items():
        if u0 - 1e-3 <= u <= u1 + 1e-3 and v0 - 1e-3 <= v <= v1 + 1e-3:
            base = name.split('_')[0]
            if base == 'torso':
                return 'shoulder' if c[2] > 1.30 else 'shirt'
            return base
    return 'other'


BD = {}
for tag, path in G.items():
    g, b, prims = mesh_data(path); st = glb_info.info(path); ims = images(g, b); rec = {'bytes': path.stat().st_size, 'triangles': st['triangles'], 'attribute_vertices': st['attribute_vertices'], 'primitives': st['primitives'],
                                                                                     'images': ims, 'image_bytes': sum(i['bytes'] for i in ims), 'joints': st['skins'][0]['joints'], 'clips': len(st['animations']), 'head': {}, 'body': {}, 'hair': 0, 'weights': {}}
    for p in prims:
        C = p['P'][p['T']].mean(1)
        if 'Head' in p['material']:
            for c in C:
                r = head_region(c); rec['head'][r] = rec['head'].get(r, 0) + 1
        elif 'Kit' in p['material'] or 'BodySkin' in p['material']:
            UVc = p['UV'][p['T']].mean(1)
            for c, uv in zip(C, UVc):
                r = body_part(c, uv, 'Kit' in p['material']); rec['body'][r] = rec['body'].get(r, 0) + 1
        else:
            rec['hair'] += len(p['T'])
        if p['W'] is not None:
            s = p['W'].sum(1); w = rec['weights'].setdefault(p['mesh'], {'vertices': 0, 'sum_min': 9.0, 'sum_max': 0.0, 'max_influences': 0})
            w['vertices'] += len(s); w['sum_min'] = round(min(w['sum_min'], float(s.min())), 4); w['sum_max'] = round(max(w['sum_max'], float(s.max())), 4); w['max_influences'] = max(w['max_influences'], int((p['W'] > 1e-4).sum(1).max()))
    BD[tag] = rec
hc.write_json(Q/'glb_breakdown57.json', BD)


def rig(path):
    g, b = glb_info.read_glb(path); sk = g['skins'][0]; names = [g['nodes'][j]['name'] for j in sk['joints']]
    rest = {g['nodes'][j]['name']: [g['nodes'][j].get(k) for k in ('translation', 'rotation', 'scale')] for j in sk['joints']}
    ibm = accessor(g, b, sk['inverseBindMatrices']); anims = {}
    for a in g['animations']:
        ch = {}
        for c in a['channels']:
            s = a['samplers'][c['sampler']]; ch[g['nodes'][c['target']['node']]['name'] + '.' + c['target']['path']] = (accessor(g, b, s['input']), accessor(g, b, s['output']))
        anims[a['name']] = ch
    return names, rest, ibm, anims


def compare(A, B):
    n0, r0, i0, a0 = rig(A); n1, r1, i1, a1 = rig(B); diff = {}
    for name in sorted(set(a0) & set(a1)):
        for k in sorted(set(a0[name]) & set(a1[name])):
            (t0, v0), (t1, v1) = a0[name][k], a1[name][k]
            d = float(np.abs(v0 - v1).max()) if v0.shape == v1.shape else float('inf')
            if d > 1e-5 or t0.shape != t1.shape:
                diff.setdefault(name, {})[k] = round(d, 4)
    return {'a': A.name, 'b': B.name, 'joint_names_and_order_equal': n0 == n1, 'rest_trs_equal': r0 == r1, 'inverse_bind_max_abs_diff': float(np.abs(i0 - i1).max()) if i0.shape == i1.shape else None,
            'clip_names_equal': sorted(a0) == sorted(a1), 'channels': sum(len(v) for v in a1.values()), 'channels_that_differ': diff}


RI = {'HM56_vs_HM57': compare(G['HM56'], G['HM57']), 'HM57_vs_LITE': compare(G['HM57'], G['HM57L'])}; hc.write_json(Q/'rig_identity57.json', RI)
vm = J('verify_motion57.json'); v = J('verify_hm55.json'); gv = J('gltf_validator.json'); wr = J('webtest57_result.json'); av = J('anim_video57.json'); bj = J('build_hm55.json')
bl_ = J('build_lite57.json')
if bj and bl_:
    bj.setdefault('lod', {'applied': {}}); bj['lod']['applied'].update(bl_.get('lod', {}).get('applied', {}))
T3 = list(G); L = ['# HM57 QA 表（スクリプト出力の実測値）\n', '代表 1 体。HM56 = 顔 P0 × 髪 H2 × ユニフォーム A（改善前）。HM57 = 顔 P0 × 髪 H1 × ユニフォーム A。軽量版 = HM57 のスマホ向け。すべて書き出した GLB を読み直して測っています。\n']
row = lambda lab, f: L.append(f'| {lab} | ' + ' | '.join(str(f(BD[t])) for t in T3) + ' |')
L.append('## 1. 容量と構成\n'); L.append('| | ' + ' | '.join(NAME[t] for t in T3) + ' |'); L.append('|---|---|---|---|')
row('GLB（バイト）', lambda r: f"{r['bytes']:,}"); row('うちテクスチャ（バイト）', lambda r: f"{r['image_bytes']:,}"); row('テクスチャ以外（バイト）', lambda r: f"{r['bytes'] - r['image_bytes']:,}")
row('三角形', lambda r: f"{r['triangles']:,}"); row('属性頂点', lambda r: f"{r['attribute_vertices']:,}"); row('プリミティブ（描画呼び出し）', lambda r: r['primitives']); row('骨', lambda r: r['joints']); row('動作クリップ', lambda r: r['clips'])
L.append('\n### テクスチャ\n'); L.append('| ' + ' | '.join(NAME[t] for t in T3) + ' |'); L.append('|---|---|---|')
mx = max(len(BD[t]['images']) for t in T3)
for i in range(mx):
    L.append('| ' + ' | '.join((lambda im: f"{im['name']} {im['px'][0]}×{im['px'][1]} {im['mime'].split('/')[1].upper()} {im['bytes']:,}")(BD[t]['images'][i]) if i < len(BD[t]['images']) else '' for t in T3) + ' |')
L.append('\n## 2. 三角形の配分\n'); L.append('### 頭（顔・首・耳）\n'); L.append('| 部位 | ' + ' | '.join(NAME[t] for t in T3) + ' |'); L.append('|---|---|---|---|')
for k, lab in HEAD_REGIONS:
    L.append(f'| {lab} | ' + ' | '.join(str(BD[t]['head'].get(k, 0)) for t in T3) + ' |')
L.append('| **頭の合計** | ' + ' | '.join(str(sum(BD[t]['head'].values())) for t in T3) + ' |')
L.append('\n### 体（ユニフォーム＋腕脚の肌）\n'); L.append('| 部位 | ' + ' | '.join(NAME[t] for t in T3) + ' |'); L.append('|---|---|---|---|')
for k, lab in BODY_PARTS:
    L.append(f'| {lab} | ' + ' | '.join(str(BD[t]['body'].get(k, 0)) for t in T3) + ' |')
L.append('| **体の合計** | ' + ' | '.join(str(sum(BD[t]['body'].values())) for t in T3) + ' |'); L.append('| 髪 | ' + ' | '.join(str(BD[t]['hair']) for t in T3) + ' |')
if bj and bj.get('lod'):
    L.append('\n生成時の三角形（間引き前 → 後）: ' + '、'.join(f"{k} {r['before']}→{r['after']}" for k, r in bj['lod']['applied'].items()))
L.append('\n## 3. 骨・ウェイト・動作（GLB を直接読んで比較）\n')
for k, r in RI.items():
    L.append(f"- **{k}**: 骨の名前と順番が同じ {r['joint_names_and_order_equal']}、静止姿勢が同じ {r['rest_trs_equal']}、逆バインド行列の最大差 {r['inverse_bind_max_abs_diff']}、クリップ名が同じ {r['clip_names_equal']}、チャンネル {r['channels']} 本")
    if r['channels_that_differ']:
        for clip, chs in r['channels_that_differ'].items():
            L.append(f"  - {clip}: 値が変わったチャンネル " + '、'.join(f'{c}（最大差 {d}）' for c, d in chs.items()))
    else:
        L.append('  - 全チャンネルの値が一致')
L.append('\n| メッシュ | ' + ' | '.join(NAME[t] for t in T3) + ' |'); L.append('|---|---|---|---|')
for mname in sorted({m.split('_')[-1] for t in T3 for m in BD[t]['weights']}):
    cells = []
    for t in T3:
        w = next((x for m, x in BD[t]['weights'].items() if m.endswith(mname)), None)
        cells.append(f"頂点 {w['vertices']}、合計 {w['sum_min']}〜{w['sum_max']}、最大 {w['max_influences']} 骨" if w else '-')
    L.append(f'| {mname} | ' + ' | '.join(cells) + ' |')
if bj and bj.get('ground_pass'):
    L.append('\n接地の補正（HM57 で追加、各コマで腰の高さを調整）: ' + '、'.join(f"{a} {g['hips_dz_mm'][0]}〜{g['hips_dz_mm'][1]}mm" + (f"（蹴り足の膝を最大 {g['swing_knee_extra_deg_max']}° 追加で曲げたコマ {g['swing_knee_frames']}）" if 'swing_knee_extra_deg_max' in g else '') for a, g in bj['ground_pass'].items()))
NAMES = {'collar': '隙間 襟→首 mm', 'sleeve_hem': '隙間 袖口→腕 mm', 'shorts_hem': '隙間 パンツの裾→太もも mm', 'sock_top': '隙間 ソックスの口→脚 mm'}
if vm:
    L.append('\n## 4. 動作中の全コマ：つぶれ・貫通・接地\n')
    L.append('測定（各コマで姿勢を付けた頂点から）: 隙間 = 服の縁から肌の表面まで。貫通 = 肌と服の三角形が交差している対の数の最大（交差したコマ数）。見通し = 襟の隙間を斜め上から通した光線が肌に当たらない本数（51 本中）。'
             '折れ = 支配的な骨で回した法線と、実際の法線が逆向きになった三角形の数（関節のつぶれ・折れ込み）。太さ = 関節から 2〜8cm の表面の、関節中心までの距離の静止時に対する比（1% 点）。'
             '足の最低点 = スパイクの一番低い点の高さ（負 = 地面にめり込み）。接地中の滑り = 最低点が 12mm 未満のコマ間で、その点が地面を動く速さ。\n')
    mods = {'HM56': G['HM56'].name, 'HM57': G['HM57'].name, 'HM57L': G['HM57L'].name}
    for act in vm['models'][mods['HM57']]['actions']:
        A = {t: vm['models'][mods[t]]['actions'][act] for t in T3}; L.append(f"### {act}（{A['HM57']['n_frames']} コマ）\n"); L.append('| 項目 | ' + ' | '.join(NAME[t] for t in T3) + ' |'); L.append('|---|---|---|---|')
        for c, lab in NAMES.items():
            L.append(f'| {lab} | ' + ' | '.join((f"{A[t]['edges'][c]['min_mm']}〜{A[t]['edges'][c]['max_mm']}" if c in A[t]['edges'] else '-') for t in T3) + ' |')
        keys = sorted({k for t in T3 for k in A[t]['pairs_max']})
        for k in keys:
            L.append(f'| 貫通 {k} | ' + ' | '.join((f"{A[t]['pairs_max'][k]}（{A[t]['pairs_frames'][k]}）" if k in A[t]['pairs_max'] else '0') for t in T3) + ' |')
        if not keys:
            L.append('| 貫通 | 0 | 0 | 0 |')
        L.append('| 見通し | ' + ' | '.join(str(A[t]['see_through_max']) for t in T3) + ' |')
        L.append('| 折れ（胴体 / 頭） | ' + ' | '.join(f"{A[t]['folded_triangles_max']['body']} / {A[t]['folded_triangles_max']['head']}" for t in T3) + ' |')
        for j, lab in (('knee', '膝'), ('elbow', '肘'), ('hip', '股関節'), ('shoulder', '肩')):
            L.append(f'| 太さ {lab} | ' + ' | '.join(str(A[t]['joint_thickness_min'][j]) for t in T3) + ' |')
        L.append('| 足の最低点 L / R mm | ' + ' | '.join(f"{A[t]['foot_min_z_mm']['L']} / {A[t]['foot_min_z_mm']['R']}" for t in T3) + ' |')
        L.append('| 接地中の滑り L / R m/s（平均） | ' + ' | '.join(' / '.join(str(A[t]['planted_foot_slide'][s]['mean_m_per_s']) for s in 'LR') for t in T3) + ' |')
        L.append('| 腰の高さ m | ' + ' | '.join(f"{A[t]['hips_z_range_m'][0]}〜{A[t]['hips_z_range_m'][1]}" for t in T3) + ' |')
        L.append('| 頭の伸び 1% / 99% | ' + ' | '.join(f"{A[t]['stretch_head_p01_min']} / {A[t]['stretch_head_p99_max']}" for t in T3) + ' |\n')
if v and v.get('hair'):
    L.append('## 5. 髪・肌色（HM57）\n'); L.append('| GLB | 頭との交差 | 生え際の浮き 中央値 / 最大 mm | 耳まわり最大 mm | 耳までの最短 mm |'); L.append('|---|---|---|---|---|')
    for k, h in v['hair'].items():
        L.append(f"| {k} | {h['hair_vs_head_intersections']} | {h['hairline_edge_height_mm']['median']} / {h['hairline_edge_height_mm']['max']} | {h['hairline_edge_height_near_ears_mm']['max']} | {h['hair_to_ear_min_distance_mm']} |")
    for f, s in (v.get('skin_colour') or {}).items():
        d = s['deltaE76']; L.append(f"\n肌の色差 ΔE76（{f}）: 首と前腕 {d['neck_vs_forearm']}、首と膝 {d['neck_vs_knee']}、首と頬 {d['neck_vs_cheek']}")
if gv:
    L.append('\n## 6. glTF Validator\n'); L.append('| ファイル | エラー | 警告 | 警告の種類 |'); L.append('|---|---|---|---|')
    for f, r in sorted(gv.items()):
        L.append(f"| {f} | {r['errors']} | {r['warnings']} | {', '.join(sorted({m.split()[1] for m in r.get('messages', []) if m.startswith('W ')})) or '-'} |")
if wr:
    L.append('\n## 7. ブラウザ（three.js、ヘッドレス Chromium + SwiftShader、GPU なし・実機ではない）\n')
    L.append(f"three.js {wr['three']}、ページのエラー {len(wr['page_errors'])} 件\n")
    for m, r in wr['models'].items():
        L.append(f"- {m}: スキン付きメッシュ {r['skinned']}、骨 {r['bones']}、動作 {len(r['clips'])}、連続再生したコマ数 " + '、'.join(f"{k.replace('TM_HM55_', '')} {n}" for k, n in r['playback'].items()))
    sw = wr.get('swap', {})
    if sw:
        a = sw['assemble']; L.append(f"- 部品の差し替え: 胴体・頭・髪のモジュール GLB（{', '.join(sw['modules'])}）を読み込み、頭と髪を胴体の骨に名前で付け替え: {a['rebound']} メッシュ、見つからない骨 {len(a['missing'])}、三角形 {a['tris']}")
        L.append('- 組み立てた選手と、モジュールから組んだ選手の画素差（同じ姿勢）: ' + '、'.join(f"{k.replace('TM_HM55_', '')} {d}%" for k, d in sw['diff_vs_player_pct'].items()))
        L.append(f"- ユニフォームの差し替え: キット B の材質に置き換え {sw['kit_swap']['replaced']} 箇所（{sw['kit_swap']['material']}）")
    for k, p in wr.get('perf', {}).items():
        L.append(f"- 22 体同時（{k}）: 描画呼び出し {p['calls']}、三角形 {p['triangles']:,}、1 コマ {p['ms_per_frame']:.2f}ms（{p['gl_renderer']}、ソフトウェア描画の参考値で、iPhone の性能ではありません）")
if av:
    L.append('\n## 8. 動画\n')
    for n, o in av.get('outputs', {}).items():
        st = (o.get('ffprobe') or {}).get('streams', [{}])[0]
        L.append(f"- {n}: {o['bytes']:,} バイト" + (f"、{st.get('codec_name')} {st.get('profile')} {st.get('width')}×{st.get('height')} {st.get('pix_fmt')} {st.get('nb_frames')} コマ" if st else ''))
(Q/'QA_TABLES57.md').write_text('\n'.join(L) + '\n'); print('SUMMARY OK'); hc.finish()
