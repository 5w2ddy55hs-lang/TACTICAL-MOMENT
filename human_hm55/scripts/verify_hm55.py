"""HM55 verification on the EXPORTED player GLBs (re-imported into an empty scene).
  1. structure: triangles, primitives, materials / alpha modes, skin joints, animations, weights
  2. neck (priority 1): for every frame of every motion - collar-to-neck gap, neck/shirt triangle intersections,
     see-through rays at the collar, edge stretch of the skinned meshes
  3. cloth: skin triangles crossing kit triangles per frame (thigh/shorts, arm/sleeve ...)
  4. hair / ears (priority 3): hair-head intersections, hairline edge height above the skin, clearance to the ears
  5. skin colour (priority 2): neck / cheek / arm / thigh texel means of the final textures, Lab differences
Writes $HM_BUILD/qa/verify_hm55.json."""
import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import hm_common as hc, hm_body as hb, hm_head as hh, hm_hair as hx, hm_texture as tx, hm_glbscene as gs, hm_assemble as ha, glb_info

OUT = hc.BUILD; PL = OUT/'models/players'
ACTIONS = ['Idle', 'Run', 'Kick', 'LookAround', 'ThrowIn', 'Header']
FULL = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
MOTION_PLAYERS = [p for p in FULL if p.endswith('.glb')] or None


def bvh(V, T):
    return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], all_triangles=True, epsilon=0.0)


def lab(rgb):
    c = np.asarray(rgb, float); c = np.where(c > 0.04045, ((c + 0.055)/1.055)**2.4, c/12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]); x, y, z = (M @ c)/np.array([0.95047, 1.0, 1.08883])
    f = lambda t: t**(1/3) if t > 0.008856 else 7.787*t + 16/116
    return np.array([116*f(y) - 16, 500*(f(x) - f(y)), 200*(f(y) - f(z))])


def match_rest(V, pts, tol=2e-4):
    idx = []
    for p in pts:
        d = np.linalg.norm(V - p, axis=1); idx += list(np.where(d < tol)[0])
    return sorted(set(idx))


def edge_list(T):
    E = set()
    for a, b, c in T:
        E.update({(min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(a, c), max(a, c))})
    return np.array(sorted(E))


def motion_checks(glb):
    arm, meshes = gs.load_player(glb); ob = {m.name: m for m in meshes}; body = ob[ha.BODY_OBJ]; head = ob[ha.HEAD_OBJ]; hair = ob.get(ha.HAIR_OBJ)
    gs.pose(arm); Vb0, Tb, Mb = gs.world_vertices(body); Vh0, Th, _ = gs.world_vertices(head)
    kit_slot = [i for i, s in enumerate(body.material_slots) if 'Kit' in s.material.name][0]
    Tkit = [t for t, m in zip(Tb, Mb) if m == kit_slot]; Tskin = [t for t, m in zip(Tb, Mb) if m != kit_slot]
    col_idx = match_rest(Vb0, hb.collar_ring(hb.ANG16)); Eb = edge_list(Tb); Eh = edge_list(Th); Lb0 = np.linalg.norm(Vb0[Eb[:, 0]] - Vb0[Eb[:, 1]], axis=1); Lh0 = np.linalg.norm(Vh0[Eh[:, 0]] - Vh0[Eh[:, 1]], axis=1)
    # torso-only triangles for the neck test (collar region): kit triangles with any vertex above z 1.30 in rest
    Ttorso = [t for t in Tkit if max(Vb0[list(t), 2]) > 1.30 and max(abs(Vb0[list(t), 0])) < 0.26]
    def region(t):
        c = Vb0[list(t)].mean(0); x, z = abs(c[0]), c[2]
        if z > 1.0 or x > 0.215:
            return 'hand' if z < 0.93 and x > 0.215 else ('arm' if x > 0.19 else 'shirt')
        return 'shirt_hem' if z > 0.86 else ('shorts' if z > 0.62 else ('knee_thigh' if z > 0.455 else ('sock' if z > 0.14 else 'boot')))
    skin_region = [region(t) for t in Tskin]; kit_region = [('sleeve' if (abs(Vb0[list(t)].mean(0)[0]) > 0.19 and Vb0[list(t)].mean(0)[2] > 1.2) else region(t)) for t in Tkit]
    res = {'collar_vertices': len(col_idx), 'actions': {}}
    def frame_metrics():
        Vb, _, _ = gs.world_vertices(body); Vh, _, _ = gs.world_vertices(head); bh = bvh(Vh, Th)
        gaps = []
        for i in col_idx:
            loc, n, k, d = bh.find_nearest(Vector(Vb[i])); gaps.append(d)
        bt = bvh(Vb, Ttorso); inter = len(bh.overlap(bt))
        # see-through: from several directions above the collar, a ray through the middle of the gap must reach skin
        chest_up = Vb[col_idx].mean(0); miss = 0; tot = 0
        for i in col_idx[::2]:
            loc, n, k, d = bh.find_nearest(Vector(Vb[i])); mid = (Vb[i] + np.array(loc))/2
            out_dir = Vb[i] - chest_up; out_dir[2] = 0; out_dir /= max(np.linalg.norm(out_dir), 1e-9)
            for elev in (35, 60, 85):
                e = math.radians(elev); dvec = -(out_dir*math.cos(e) + np.array([0, 0, 1.0])*math.sin(e)); o = mid - dvec*0.25
                hit = bh.ray_cast(Vector(o), Vector(dvec), 0.25 + 0.09); tot += 1; miss += hit[0] is None
        bs = bvh(Vb, Tskin); bk_ = bvh(Vb, Tkit); prs = bs.overlap(bk_); cloth = len(prs); kinds = {}
        for i, j in prs:
            k = skin_region[i] + ' x ' + kit_region[j]; kinds[k] = kinds.get(k, 0) + 1
        sb = np.linalg.norm(Vb[Eb[:, 0]] - Vb[Eb[:, 1]], axis=1)/np.maximum(Lb0, 1e-9); sh = np.linalg.norm(Vh[Eh[:, 0]] - Vh[Eh[:, 1]], axis=1)/np.maximum(Lh0, 1e-9)
        ib = int(np.argmax(sb)); ih = int(np.argmin(sh)); loc = lambda V0, E, i: [round(float(x), 3) for x in (V0[E[i, 0]] + V0[E[i, 1]])/2]
        return {'gap_min_mm': float(min(gaps))*1000, 'gap_max_mm': float(max(gaps))*1000, 'neck_shirt_intersections': inter, 'see_through_misses': miss, 'see_through_rays': tot,
                'skin_cloth_intersections': cloth, 'skin_cloth_kinds': kinds, 'stretch_body_max': float(sb.max()), 'stretch_body_max_at_rest_xyz': loc(Vb0, Eb, ib), 'stretch_head_max': float(sh.max()),
                'stretch_head_min': float(sh.min()), 'stretch_head_min_at_rest_xyz': loc(Vh0, Eh, ih), 'stretch_body_p99': float(np.percentile(sb, 99)), 'stretch_head_p01': float(np.percentile(sh, 1)), 'stretch_head_p99': float(np.percentile(sh, 99))}
    res['rest'] = frame_metrics()
    for act in ACTIONS:
        a = next(x for x in bpy.data.actions if x.name.startswith('TM_HM55_' + act)); f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1])); rows = []
        for f in range(f0, f1 + 1):
            gs.pose(arm, 'TM_HM55_' + act, f); m = frame_metrics(); m['frame'] = f
            hq = arm.pose.bones['Head'].matrix.to_3x3() @ arm.pose.bones['Chest'].matrix.to_3x3().inverted(); m['head_vs_chest_deg'] = math.degrees(hq.to_quaternion().angle); rows.append(m)
        worst_gap = min(rows, key=lambda r: r['gap_min_mm']); wide = max(rows, key=lambda r: r['gap_max_mm'])
        res['actions'][act] = {'frames': [f0, f1], 'head_vs_chest_deg_max': round(max(r['head_vs_chest_deg'] for r in rows), 1),
                               'gap_min_mm': round(worst_gap['gap_min_mm'], 2), 'gap_min_frame': worst_gap['frame'], 'gap_max_mm': round(wide['gap_max_mm'], 2), 'gap_max_frame': wide['frame'],
                               'neck_shirt_intersections_max': max(r['neck_shirt_intersections'] for r in rows), 'see_through_misses_max': max(r['see_through_misses'] for r in rows), 'see_through_rays': rows[0]['see_through_rays'],
                               'skin_cloth_intersections_max': max(r['skin_cloth_intersections'] for r in rows), 'skin_cloth_frames_with_any': sum(r['skin_cloth_intersections'] > 0 for r in rows),
                               'skin_cloth_kinds_at_worst_frame': max(rows, key=lambda r: r['skin_cloth_intersections'])['skin_cloth_kinds'], 'skin_cloth_worst_frame': max(rows, key=lambda r: r['skin_cloth_intersections'])['frame'],
                               'stretch_body_max_at_rest_xyz': max(rows, key=lambda r: r['stretch_body_max'])['stretch_body_max_at_rest_xyz'], 'stretch_body_p99_max': round(max(r['stretch_body_p99'] for r in rows), 2),
                               'stretch_head_min_at_rest_xyz': min(rows, key=lambda r: r['stretch_head_min'])['stretch_head_min_at_rest_xyz'], 'stretch_head_p01_min': round(min(r['stretch_head_p01'] for r in rows), 2), 'stretch_head_p99_max': round(max(r['stretch_head_p99'] for r in rows), 2),
                               'stretch_body_max': round(max(r['stretch_body_max'] for r in rows), 2), 'stretch_head_max': round(max(r['stretch_head_max'] for r in rows), 2), 'stretch_head_min': round(min(r['stretch_head_min'] for r in rows), 2)}
    for k in ('gap_min_mm', 'gap_max_mm'):
        res['rest'][k] = round(res['rest'][k], 2)
    # weights of the re-imported meshes
    w = {}
    for m in meshes:
        sums = [sum(g.weight for g in v.groups) for v in m.data.vertices]; cnt = [len([g for g in v.groups if g.weight > 0]) for v in m.data.vertices]
        w[m.name] = {'vertices': len(sums), 'weight_sum_min': round(min(sums), 4), 'weight_sum_max': round(max(sums), 4), 'max_influences': max(cnt)}
    res['weights'] = w
    return res


def hair_checks(glb):
    arm, meshes = gs.load_player(glb); ob = {m.name: m for m in meshes}; gs.pose(arm); head = ob[ha.HEAD_OBJ]; hair = ob[ha.HAIR_OBJ]
    Vh, Th, _ = gs.world_vertices(head); Vx, Tx, Mx = gs.world_vertices(hair); bh = bvh(Vh, Th); bx = bvh(Vx, Tx)
    face = Path(glb).name.split('_')[3]; P = hh.FACES[face]['P']; C = hh.scalp_centre(P) + hb.HEAD_PIVOT
    # ear triangles = head triangles whose vertices are all farther out than the skull grid (separate shells): take by rest region via |x| and connectivity
    hd = ha.head_data(P); ear_first = min(hd['ears'][s]['first'] for s in (1, -1)); earV = hd['verts'][ear_first:] + hb.HEAD_PIVOT; skullV = hd['verts'][:ear_first] + hb.HEAD_PIVOT
    skullT = [(f[0], f[k], f[k + 1]) for f, r in zip(hd['faces'], hd['face_region']) if r == 'head' for k in range(1, len(f) - 1)]; bskull = bvh(skullV, skullT)
    # free boundary of the scalp layer (cap + edge band), merged by position
    names = [s.material.name for s in hair.material_slots]; cap_slots = [i for i, n in enumerate(names) if n.endswith('_Cap') or n.endswith('_CapEdge')]
    Tcap = [t for t, m in zip(Tx, Mx) if m in cap_slots]; key = np.round(Vx/1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    import collections
    E = collections.Counter()
    for t in Tcap:
        a = inv[list(t)]
        for i, j in ((0, 1), (1, 2), (2, 0)):
            E[(min(a[i], a[j]), max(a[i], a[j]))] += 1
    bnd = set(v for (u, v_), c in E.items() if c == 1 for v in (u, v_)); edge_idx = [i for i in range(len(Vx)) if inv[i] in bnd]
    hts = []; ear_sector = []
    for i in edge_idx:
        p = Vx[i]; d = p - C; r = np.linalg.norm(d); d = d/r; loc = bskull.ray_cast(Vector(C + d*0.5), Vector(-d), 0.5)[0]
        if loc is None:
            continue
        h = (r - (np.array(loc) - C) @ d)*1000; az = abs(math.degrees(math.atan2(d[0], -d[1]))); hts.append(h)
        if 58 <= az <= 102:
            ear_sector.append(h)
    # hair to ear clearance: nearest distance from ear vertices to the hair surface
    dmin = min(bx.find_nearest(Vector(p))[3] for p in earV)
    return {'hair_triangles': len(Tx), 'hair_vs_head_intersections': len(bx.overlap(bh)), 'hairline_edge_vertices': len(edge_idx),
            'hairline_edge_height_mm': {'min': round(float(np.min(hts)), 2), 'median': round(float(np.median(hts)), 2), 'max': round(float(np.max(hts)), 2)},
            'hairline_edge_height_near_ears_mm': {'median': round(float(np.median(ear_sector)), 2), 'max': round(float(np.max(ear_sector)), 2), 'vertices': len(ear_sector)},
            'hair_to_ear_min_distance_mm': round(float(dmin)*1000, 2)}


def skin_colour():
    from PIL import Image
    body = hb.body_data(); out = {}
    faces = [f for f, m in zip(body['faces'], body['face_material']) if m == 'skin']; li = 0; uvs = []
    for f, m in zip(body['faces'], body['face_material']):
        if m == 'skin':
            uvs += [tuple(u) for u in body['uvs'][li:li + len(f)]]
        li += len(f)
    r = tx.rasterize(body['verts'], faces, uvs, 512); z = r['pos'][..., 2]; x = np.abs(r['pos'][..., 0]); m = r['mask']
    arm_m = m & (x > 0.20) & (z > 0.98) & (z < 1.10); thigh_m = m & (x < 0.19) & (z > 0.50) & (z < 0.58)       # forearm and knee: away from the sleeve / shorts hems
    for f in hh.FACES:
        tone = tx.FACE_TEX[f]['tone']; hd = ha.head_data(hh.FACES[f]['P']); reg = {'head': 0, 'ear_L': 1, 'ear_R': 2}
        rh = tx.rasterize(hd['verts'], hd['faces'], [tuple(u) for u in hd['uvs']], 1024, [reg[n] for n in hd['face_region']]); zh = rh['pos'][..., 2]; sz = hd['P']['scale'][2]
        neck = rh['mask'] & (rh['fid'] == 0) & (zh < -0.085) & (zh > -0.130); cheek = rh['mask'] & (rh['fid'] == 0) & (np.abs(zh - 0.004*sz) < 0.012) & (np.abs(np.abs(rh['pos'][..., 0]) - 0.050) < 0.010) & (rh['pos'][..., 1] < -0.04)
        H = np.asarray(Image.open(OUT/f'textures/TM_HM55_Head_{f}.png').convert('RGB'), float)/255; B = np.asarray(Image.open(OUT/f'textures/TM_HM55_BodySkin_{tone}.png').convert('RGB'), float)/255
        mean = {'neck': H[neck].mean(0), 'cheek': H[cheek].mean(0), 'forearm': B[arm_m].mean(0), 'knee': B[thigh_m].mean(0)}; L = {k: lab(v) for k, v in mean.items()}
        out[f] = {'tone': tone, 'mean_srgb': {k: [round(float(c), 4) for c in v] for k, v in mean.items()},
                  'deltaE76': {'neck_vs_forearm': round(float(np.linalg.norm(L['neck'] - L['forearm'])), 2), 'neck_vs_knee': round(float(np.linalg.norm(L['neck'] - L['knee'])), 2),
                               'neck_vs_cheek': round(float(np.linalg.norm(L['neck'] - L['cheek'])), 2)}}
    return out


R = {'status': hc.STATUS, 'blender': bpy.app.version_string, 'structure': {}, 'motion': {}, 'hair': {}}
glbs = sorted(PL.glob('*.glb'))
for g in glbs:
    R['structure'][g.name] = glb_info.info(g)
motion_set = [PL/n for n in MOTION_PLAYERS] if MOTION_PLAYERS else [g for g in glbs if 'KITA' in g.name and g.name.split('_')[4] == 'H2'] or glbs[:1]
for g in motion_set:
    R['motion'][g.name] = motion_checks(g); print('motion', g.name, json.dumps({k: (v['gap_min_mm'], v['gap_max_mm'], v['neck_shirt_intersections_max'], v['see_through_misses_max'], v['skin_cloth_intersections_max']) for k, v in R['motion'][g.name]['actions'].items()}), flush=True)
for g in [g for g in glbs if 'KITA' in g.name]:
    R['hair'][g.name] = hair_checks(g); print('hair', g.name, R['hair'][g.name], flush=True)
R['skin_colour'] = skin_colour(); print('skin', json.dumps(R['skin_colour']), flush=True)
hc.write_json(OUT/'qa/verify_hm55.json', R); print('VERIFY OK'); hc.finish()
