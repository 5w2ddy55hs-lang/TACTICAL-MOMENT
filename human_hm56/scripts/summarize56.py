"""HM56 QA tables (Markdown) generated from $HM_BUILD/qa/*.json plus the two exported GLBs - no hand-copied numbers.
Also compares the skeleton and the 6 clips of HM55 and HM56 byte for byte (no Blender: GLB JSON + binary chunk).
Usage: HM_BUILD=... python summarize56.py <HM55 glb> <HM56 glb>; writes qa/rig_identity56.json and qa/QA_TABLES56.md."""
import sys, json, struct, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import hm_common as hc, glb_info

OLD, NEW = Path(sys.argv[1]), Path(sys.argv[2])
Q = hc.BUILD/'qa'; J = lambda n: json.loads((Q/n).read_text()) if (Q/n).exists() else None
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}; CT = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}


def accessor(g, b, i):
    a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]; n = a['count']*NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); assert 'byteStride' not in bv or bv['byteStride'] == NC[a['type']]*4
    return np.array(struct.unpack_from('<%d%s' % (n, CT[a['componentType']]), b, off)).reshape(a['count'], -1)


def rig(path):
    g, b = glb_info.read_glb(path); sk = g['skins'][0]; names = [g['nodes'][j]['name'] for j in sk['joints']]
    rest = {g['nodes'][j]['name']: [g['nodes'][j].get(k) for k in ('translation', 'rotation', 'scale')] for j in sk['joints']}
    ibm = accessor(g, b, sk['inverseBindMatrices']); anims = {}
    for a in g['animations']:
        ch = {}
        for c in a['channels']:
            s = a['samplers'][c['sampler']]; key = g['nodes'][c['target']['node']]['name'] + '.' + c['target']['path']
            ch[key] = (accessor(g, b, s['input']), accessor(g, b, s['output']), s.get('interpolation', 'LINEAR'))
        anims[a['name']] = ch
    return names, rest, ibm, anims


def compare():
    n0, r0, i0, a0 = rig(OLD); n1, r1, i1, a1 = rig(NEW)
    res = {'old': OLD.name, 'new': NEW.name, 'old_sha256': hc.sha256(OLD), 'new_sha256': hc.sha256(NEW), 'joints_old': len(n0), 'joints_new': len(n1),
           'joint_names_and_order_equal': n0 == n1, 'rest_trs_equal': r0 == r1, 'inverse_bind_max_abs_diff': float(np.abs(i0 - i1).max()) if i0.shape == i1.shape else None,
           'clips_old': sorted(a0), 'clips_new': sorted(a1), 'clip_names_equal': sorted(a0) == sorted(a1), 'channels': 0, 'channel_set_equal': True,
           'time_max_abs_diff': 0.0, 'value_max_abs_diff': 0.0, 'interpolation_equal': True, 'per_clip': {}}
    for name in sorted(set(a0) & set(a1)):
        c0, c1 = a0[name], a1[name]; res['channel_set_equal'] &= set(c0) == set(c1); td = vd = 0.0
        for k in set(c0) & set(c1):
            t0, v0, p0 = c0[k]; t1, v1, p1 = c1[k]; res['channels'] += 1; res['interpolation_equal'] &= p0 == p1
            td = max(td, float(np.abs(t0 - t1).max()) if t0.shape == t1.shape else float('inf')); vd = max(vd, float(np.abs(v0 - v1).max()) if v0.shape == v1.shape else float('inf'))
        res['per_clip'][name] = {'channels': len(c1), 'keys': int(len(next(iter(c1.values()))[0])), 'time_max_abs_diff': td, 'value_max_abs_diff': vd}
        res['time_max_abs_diff'] = max(res['time_max_abs_diff'], td); res['value_max_abs_diff'] = max(res['value_max_abs_diff'], vd)
    res['identical'] = (res['joint_names_and_order_equal'] and res['rest_trs_equal'] and res['inverse_bind_max_abs_diff'] == 0.0 and res['clip_names_equal']
                        and res['channel_set_equal'] and res['interpolation_equal'] and res['time_max_abs_diff'] == 0.0 and res['value_max_abs_diff'] == 0.0)
    hc.write_json(Q/'rig_identity56.json', res); return res


ri = compare(); vm = J('verify_motion56.json'); v = J('verify_hm55.json'); gv = J('gltf_validator.json'); wr = J('webtest55_result.json'); av = J('anim_video56.json')
L = ['# HM56 QA 表（スクリプト出力の実測値）\n', '代表 1 体（顔 P0 × 髪 H2 × ユニフォーム A）。改良前 = HM55 の同じ組み合わせ。どちらも書き出した GLB を読み直して測っています。\n']
L.append('## 1. ファイルサイズと構成\n'); L.append('| | HM55（改良前） | HM56（改良後） |'); L.append('|---|---|---|')
s0, s1 = glb_info.info(OLD), glb_info.info(NEW)
for lab, f in (('ファイルサイズ（バイト）', lambda p, s: f'{p.stat().st_size:,}'), ('三角形', lambda p, s: f"{s['triangles']:,}"), ('属性頂点', lambda p, s: f"{s['attribute_vertices']:,}"),
               ('プリミティブ', lambda p, s: s['primitives']), ('画像', lambda p, s: s['images']), ('骨（skin joints）', lambda p, s: s['skins'][0]['joints']), ('動作クリップ', lambda p, s: len(s['animations']))):
    L.append(f'| {lab} | {f(OLD, s0)} | {f(NEW, s1)} |')
L.append('\n### 材質（プリミティブ）別の三角形\n'); L.append('| 材質 | HM55 | HM56 |'); L.append('|---|---|---|')
mt = lambda s: {p['material'].replace('TM_HM55_', '').replace('TM_HM56_', ''): p['triangles'] for m in s['meshes'].values() for p in m}
m0, m1 = mt(s0), mt(s1)
for k in sorted(set(m0) | set(m1)):
    L.append(f'| {k} | {m0.get(k, "-")} | {m1.get(k, "-")} |')
L.append('\n## 2. 骨と動作が HM55 と同一か（GLB のバイナリを直接比較）\n')
L.append(f"- 骨: {ri['joints_old']} → {ri['joints_new']} 本、名前と順番が同じ: {ri['joint_names_and_order_equal']}、静止姿勢（位置・回転・拡大）が同じ: {ri['rest_trs_equal']}、逆バインド行列の最大差: {ri['inverse_bind_max_abs_diff']}")
L.append(f"- 動作: {', '.join(ri['clips_new'])}（名前が同じ: {ri['clip_names_equal']}）、チャンネル {ri['channels']} 本、時刻の最大差 {ri['time_max_abs_diff']}、値の最大差 {ri['value_max_abs_diff']}、補間が同じ: {ri['interpolation_equal']}")
L.append(f"- **判定: {'同一' if ri['identical'] else '差あり'}**（ウェイトは体形に合わせて作り直しています。下の 3 を参照）\n")
L.append('## 3. ウェイト（HM56、読み直した GLB）\n'); L.append('| メッシュ | 頂点 | 合計の最小 | 合計の最大 | 1 頂点あたりの最大影響数 |'); L.append('|---|---|---|---|---|')
for gname, ww in (v or {}).get('motion', {}).items():
    for mname, w in (ww.get('weights') or {}).items():
        L.append(f"| {mname} | {w['vertices']} | {w['weight_sum_min']} | {w['weight_sum_max']} | {w['max_influences']} |")
NAMES = {'collar': '襟 → 首', 'sleeve_hem': '袖口 → 腕', 'shorts_hem': 'パンツの裾 → 太もも', 'sock_top': 'ソックスの口 → 脚の肌'}
L.append('\n## 4. 動作中の全コマ：隙間・貫通・見通し・伸び\n')
L.append('測定: 各コマで姿勢を付けた頂点から計算。隙間 = 服の縁の各頂点から肌の表面までの最短距離（mm）。'
         '貫通 = 肌（首・腕・脚）と服の三角形が交差している対の数の最大と、交差があったコマ数。見通し = 襟の隙間を斜め上 3 方向から通した光線が肌に当たらなかった本数。'
         '伸び = 辺の長さ ÷ 静止時の長さ（頭は 1 パーセンタイルと 99 パーセンタイル）。\n')
for act in (vm or {}).get('models', {}).get(NEW.name, {}).get('actions', {}):
    a0 = vm['models'][OLD.name]['actions'][act]; a1 = vm['models'][NEW.name]['actions'][act]
    L.append(f"### {act}（{a1['n_frames']} コマ）\n"); L.append('| 項目 | HM55 | HM56 |'); L.append('|---|---|---|')
    for c in NAMES:
        e0, e1 = a0['edges'].get(c), a1['edges'].get(c)
        if e0 or e1:
            fmt = lambda e: f"{e['min_mm']}〜{e['max_mm']}" if e else '-'
            L.append(f'| 隙間 {NAMES[c]}（mm） | {fmt(e0)} | {fmt(e1)} |')
    keys = sorted(set(a0['pairs_max']) | set(a1['pairs_max']))
    fmtp = lambda a, k: f"{a['pairs_max'][k]}（{a['pairs_frames'][k]} コマ）" if k in a['pairs_max'] else '0'
    for k in keys:
        L.append(f'| 貫通 {k} | {fmtp(a0, k)} | {fmtp(a1, k)} |')
    if not keys:
        L.append('| 貫通 | 0 | 0 |')
    L.append(f"| 見通し（{a1['see_through_rays']} 本中） | {a0['see_through_max']} | {a1['see_through_max']} |")
    L.append(f"| 胴体の伸び 99% | {a0['stretch_body_p99_max']} | {a1['stretch_body_p99_max']} |")
    L.append(f"| 頭の伸び 1% / 99% | {a0['stretch_head_p01_min']} / {a0['stretch_head_p99_max']} | {a1['stretch_head_p01_min']} / {a1['stretch_head_p99_max']} |\n")
if v and v.get('hair'):
    L.append('## 5. 髪（HM56）\n'); L.append('| 組み合わせ | 頭との交差 | 生え際の縁の高さ（中央値 / 最大 mm） | 耳まわり（最大 mm） | 耳までの最短距離 mm |'); L.append('|---|---|---|---|---|')
    for k, h in v['hair'].items():
        L.append(f"| {k} | {h['hair_vs_head_intersections']} | {h['hairline_edge_height_mm']['median']} / {h['hairline_edge_height_mm']['max']} | {h['hairline_edge_height_near_ears_mm']['max']} | {h['hair_to_ear_min_distance_mm']} |")
if v and v.get('skin_colour'):
    L.append('\n## 6. 肌の色差（ΔE76、HM56）\n'); L.append('| 顔 | 首と前腕 | 首と膝 | 首と頬 |'); L.append('|---|---|---|---|')
    for f, s in v['skin_colour'].items():
        d = s['deltaE76']; L.append(f"| {f}（{s['tone']}） | {d['neck_vs_forearm']} | {d['neck_vs_knee']} | {d['neck_vs_cheek']} |")
if gv:
    L.append('\n## 7. glTF Validator\n'); L.append('| ファイル | エラー | 警告 | 情報 | 警告の内容 |'); L.append('|---|---|---|---|---|')
    for f, r in sorted(gv.items()):
        kinds = sorted({m.split()[1] for m in r.get('messages', []) if m.startswith('W ')})
        L.append(f"| {f} | {r['errors']} | {r['warnings']} | {r['infos']} | {', '.join(kinds) or '-'} |")
    L.append(f"\nValidator {next(iter(gv.values())).get('validatorVersion', '?')}。NODE_SKINNED_MESH_NON_ROOT は、スキン付きメッシュが骨組みのノードの子になっているという警告です。親のノードは移動・回転・拡大なしなので、見た目は変わりません。HM55 でも同じ警告が出ています。")
if wr:
    L.append('\n## 8. ブラウザ（three.js、ヘッドレス Chromium + SwiftShader、GPU なし）\n')
    for n, m in wr['models'].items():
        L.append(f"- {n}: three.js {wr.get('three')}、スキン付きプリミティブ {m['skinned']}、骨 {m['bones']}、動作 {len(m['clips'])} 本（{', '.join(c['name'] for c in m['clips'])}）")
        L.append('- 連続再生したコマ数: ' + '、'.join(f'{k} {v}' for k, v in m['playback'].items()))
    for k, p in wr.get('perf', {}).items():
        L.append(f"- 同時描画 {k}: 描画呼び出し {p['calls']}、三角形 {p['triangles']:,}、1 コマ {p['ms_per_frame']:.2f}ms（{p['gl_renderer']}、ソフトウェア描画の参考値）")
    L.append(f"- ページのエラー: {len(wr.get('page_errors', []))} 件")
    wa = J('webtest55_analysis.json')
    if wa:
        for n, a in wa.items():
            L.append(f"- 髪の描画順を入れ替えたときに変わった画素: {a['order_changed_pixels_pct']} %、片面表示と両面表示の差: {a['front_only_vs_double_sided_changed_pixels_pct']} %")
if av:
    L.append('\n## 9. 連続再生の動画\n'); L.append('```'); L.append(json.dumps({k: av[k] for k in av if k != 'ffprobe_full'}, ensure_ascii=False, indent=1)[:2000]); L.append('```')
(Q/'QA_TABLES56.md').write_text('\n'.join(L) + '\n'); print('SUMMARY OK identical=%s' % ri['identical']); hc.finish()
