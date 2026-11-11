"""Model-agnostic motion verification of an exported player GLB (works the same on HM55, HM56, HM57 and HM57 LITE).
For EVERY frame of every action:
  - open cloth edges (collar, sleeve hems, shirt hem, shorts hems, sock tops, boot tops) are found from the mesh
    itself (boundary loops of the kit material at rest) and their distance to the skin is measured
    (min = how close the hem comes to / into the skin, max = widest opening);
  - skin x cloth triangle intersections, split by region (neck x shirt, arm x shirt/sleeve, knee/thigh x sock, ...);
    HM57: also cloth x cloth (shirt torso x shorts, by UV chart: navy shorts showing through the shirt hem);
  - see-through rays into the collar opening;
  - edge stretch of the skinned meshes;
  - HM57: joint collapse = triangles whose posed normal turns against the normal carried by their dominant bone
    (folds / crushing), and the thickness ratio around knees, elbows, shoulders and hips (posed distance to the joint
    centre / rest distance, 1st percentile of the surface within 2-8 cm of the joint, 3-14 cm for the hip);
  - HM57: ground contact = lowest boot point per foot per frame (negative = through the ground) and, while a foot is
    planted (lowest point < 12 mm), how fast it slides over the ground (the clips are in place: in the game the root
    has to move at this speed for the foot to stay planted).
Usage: python verify_motion57.py <out.json> <player.glb> [<player.glb> ...]"""
import sys, json, math, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import hm_common as hc, hm_glbscene as gs

ACTIONS = ['Idle', 'Run', 'Kick', 'LookAround', 'ThrowIn', 'Header']
bvh = lambda V, T: BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], all_triangles=True, epsilon=0.0)


def boundary_loops(V, T):
    key = np.round(V/1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); E = collections.Counter()
    for t in T:
        a = inv[list(t)]
        for i, j in ((0, 1), (1, 2), (2, 0)):
            E[(min(a[i], a[j]), max(a[i], a[j]))] += 1
    bv = {v for (u, w), c in E.items() if c == 1 for v in (u, w)}
    return [i for i in range(len(V)) if inv[i] in bv]


def edge_class(p):
    x, y, z = abs(p[0]), p[1], p[2]
    if z > 1.40 and x < 0.13: return 'collar'
    if z > 1.0 and x > 0.19: return 'sleeve_hem'
    if 0.80 < z < 0.95 and x < 0.21: return 'shirt_hem'
    if 0.58 < z < 0.70: return 'shorts_hem'
    if 0.38 < z < 0.50: return 'sock_top'
    if 0.10 < z < 0.20: return 'boot_top'
    return None


def tri_region(c, kind):
    x, z = abs(c[0]), c[2]
    if kind == 'head':
        return 'neck' if z < 1.56 else 'head'
    if kind == 'skin':
        if x > 0.19 and z > 0.93: return 'arm'
        if x > 0.215: return 'hand'
        return 'knee_thigh' if z > 0.455 else 'shin'
    if z > 1.30 and x < 0.17: return 'shirt_yoke'
    if x > 0.19 and z > 1.15: return 'sleeve'
    if z > 0.86: return 'shirt'
    if z > 0.62: return 'shorts'
    if z > 0.14: return 'sock'
    return 'boot'


def run(glb):
    arm, meshes = gs.load_player(glb); body = next(m for m in meshes if m.name.endswith('_Body')); head = next(m for m in meshes if m.name.endswith('_Head'))
    gs.pose(arm); Vb0, Tb, Mb = gs.world_vertices(body); Vh0, Th, _ = gs.world_vertices(head)
    kit_slot = [i for i, s in enumerate(body.material_slots) if 'Kit' in s.material.name][0]
    Tkit = [t for t, m in zip(Tb, Mb) if m == kit_slot]; Tskin = [t for t, m in zip(Tb, Mb) if m != kit_slot]
    # HM57: cloth over cloth - shirt torso x shorts, classified by the UV chart of each kit triangle (hm_body.KIT_RECT)
    import hm_body as hb_
    me = body.data; me.calc_loop_triangles(); uvl = me.uv_layers.active.data
    def chart(lt):
        u, v = np.mean([uvl[l].uv[:] for l in lt.loops], axis=0)
        return next((n.split('_')[0] for n, (u0, v0, u1, v1) in hb_.KIT_RECT.items() if u0 - 1e-3 <= u <= u1 + 1e-3 and v0 - 1e-3 <= v <= v1 + 1e-3), None)
    charts = [chart(lt) if lt.material_index == kit_slot else None for lt in me.loop_triangles]
    T_shirt = [tuple(lt.vertices) for lt, c in zip(me.loop_triangles, charts) if c == 'torso']; T_shorts = [tuple(lt.vertices) for lt, c in zip(me.loop_triangles, charts) if c == 'shorts']
    kreg = [tri_region(Vb0[list(t)].mean(0), 'kit') for t in Tkit]; sreg = [tri_region(Vb0[list(t)].mean(0), 'skin') for t in Tskin]; hreg = [tri_region(Vh0[list(t)].mean(0), 'head') for t in Th]
    edges = collections.defaultdict(list)
    for i in boundary_loops(Vb0, Tkit):
        c = edge_class(Vb0[i])
        if c:
            edges[c].append(i)
    Eb = np.array(sorted({(min(a, b), max(a, b)) for t in Tb for a, b in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2]))})); Eh = np.array(sorted({(min(a, b), max(a, b)) for t in Th for a, b in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2]))}))
    Lb0 = np.linalg.norm(Vb0[Eb[:, 0]] - Vb0[Eb[:, 1]], axis=1); Lh0 = np.linalg.norm(Vh0[Eh[:, 0]] - Vh0[Eh[:, 1]], axis=1)
    def metrics():
        Vb, _, _ = gs.world_vertices(body); Vh, _, _ = gs.world_vertices(head); bh = bvh(Vh, Th); bs = bvh(Vb, Tskin); bk = bvh(Vb, Tkit); out = {'edges': {}}
        for c, idx in edges.items():
            tree = bh if c == 'collar' else bs; d = [tree.find_nearest(Vector(Vb[i]))[3] for i in idx]
            out['edges'][c] = (float(min(d))*1000, float(max(d))*1000)
        pairs = collections.Counter()
        for i, j in bh.overlap(bk):
            pairs[hreg[i] + ' x ' + kreg[j]] += 1
        for i, j in bs.overlap(bk):
            pairs[sreg[i] + ' x ' + kreg[j]] += 1
        if T_shirt and T_shorts:
            n_ = len(bvh(Vb, T_shirt).overlap(bvh(Vb, T_shorts)))
            if n_:
                pairs['shirt x shorts (cloth)'] = n_
        out['pairs'] = dict(pairs)
        col = edges['collar']; cen = Vb[col].mean(0); miss = 0; tot = 0
        for i in col[::max(1, len(col)//14)]:
            loc = np.array(bh.find_nearest(Vector(Vb[i]))[0]); mid = (Vb[i] + loc)/2; od = Vb[i] - cen; od[2] = 0; od /= max(np.linalg.norm(od), 1e-9)
            for elev in (35, 60, 85):
                e = math.radians(elev); dv = -(od*math.cos(e) + np.array([0, 0, 1.0])*math.sin(e)); hit = bh.ray_cast(Vector(mid - dv*0.25), Vector(dv), 0.34); tot += 1; miss += hit[0] is None
        out['see_through'] = (miss, tot)
        sb = np.linalg.norm(Vb[Eb[:, 0]] - Vb[Eb[:, 1]], axis=1)/np.maximum(Lb0, 1e-9); sh = np.linalg.norm(Vh[Eh[:, 0]] - Vh[Eh[:, 1]], axis=1)/np.maximum(Lh0, 1e-9)
        out['stretch'] = (float(np.percentile(sb, 99)), float(np.percentile(sh, 1)), float(np.percentile(sh, 99)))
        return out
    # ---- HM57: joint collapse / ground contact setup (rest pose)
    JOINTS = {'knee': ('LowerLeg_L', 'LowerLeg_R'), 'elbow': ('LowerArm_L', 'LowerArm_R'), 'shoulder': ('UpperArm_L', 'UpperArm_R'), 'hip': ('UpperLeg_L', 'UpperLeg_R')}
    def dominant(ob):
        names = {g.index: g.name for g in ob.vertex_groups}
        return [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else None for v in ob.data.vertices]
    dom_b = dominant(body); dom_h = dominant(head)
    tri_n = lambda V, T: np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    TbA = np.array(Tb); ThA = np.array(Th); nb0 = tri_n(Vb0, TbA); nh0 = tri_n(Vh0, ThA)
    good_b = np.linalg.norm(nb0, axis=1) > 1e-10; good_h = np.linalg.norm(nh0, axis=1) > 1e-10
    mk_masks = lambda td: {b: np.array([d_ == b for d_ in td]) for b in set(td) if b is not None}
    tdom_b = mk_masks([dom_b[t[0]] for t in TbA]); tdom_h = mk_masks([dom_h[t[0]] for t in ThA])
    jrest = {b: gs.bone_head(arm, b) for js in JOINTS.values() for b in js}
    SHELL = lambda b: (0.03, 0.14) if b.startswith('UpperLeg') else (0.02, 0.08)       # the hip joint sits deep inside the shorts
    jshell = {b: np.where((np.linalg.norm(Vb0 - jrest[b], axis=1) > SHELL(b)[0]) & (np.linalg.norm(Vb0 - jrest[b], axis=1) < SHELL(b)[1]))[0] for b in jrest}
    boot_v = {s_: np.where((Vb0[:, 2] < 0.12) & (np.sign(Vb0[:, 0]) == (1 if s_ == 'L' else -1)))[0] for s_ in ('L', 'R')}
    def bone_rot(name):
        pb = arm.pose.bones[name]; M = (arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()); return np.array(M.to_3x3())
    def collapse_metrics():
        Vb, _, _ = gs.world_vertices(body); Vh, _, _ = gs.world_vertices(head); rot = {}; out = {'folded': {}, 'thick': {}}
        for V0n, V, TA, tdom, good, tag_ in ((nb0, Vb, TbA, tdom_b, good_b, 'body'), (nh0, Vh, ThA, tdom_h, good_h, 'head')):
            n1 = tri_n(V, TA); pred = np.zeros_like(V0n)
            for b, k in tdom.items():
                pred[k] = V0n[k] @ bone_rot(b).T
            out['folded'][tag_] = int(((np.einsum('ij,ij->i', pred, n1) < 0) & good).sum())
        for j, (bl, br) in JOINTS.items():
            vals = []
            for b in (bl, br):
                c1 = gs.bone_head(arm, b); idx = jshell[b]
                vals.append(np.percentile(np.linalg.norm(Vb[idx] - c1, axis=1)/np.linalg.norm(Vb0[idx] - jrest[b], axis=1), 1))
            out['thick'][j] = float(min(vals))
        out['foot_min_z'] = {s_: float(Vb[boot_v[s_], 2].min()) for s_ in boot_v}
        out['foot_low_xy'] = {s_: Vb[boot_v[s_]][np.argmin(Vb[boot_v[s_], 2]), :2].tolist() for s_ in boot_v}
        out['foot_bone_xy'] = {s_: gs.bone_head(arm, 'Foot_' + s_)[:2].tolist() for s_ in boot_v}
        out['hips_z'] = float(gs.bone_head(arm, 'Hips')[2]); out['hips_xy'] = gs.bone_head(arm, 'Hips')[:2].tolist()
        return out
    R = {'glb': glb.name, 'sha256': hc.sha256(glb), 'edge_vertices': {c: len(v) for c, v in edges.items()}, 'rest': metrics(), 'actions': {}}
    for act in ACTIONS:
        a = next(x for x in bpy.data.actions if x.name.startswith('TM_HM55_' + act)); f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1])); rows = []
        for f in range(f0, f1 + 1):
            gs.pose(arm, 'TM_HM55_' + act, f); m = metrics(); m['frame'] = f; m['c'] = collapse_metrics(); rows.append(m)
        agg = {'frames': [f0, f1], 'n_frames': len(rows), 'edges': {}, 'pairs_max': {}, 'pairs_frames': {}, 'see_through_max': max(r['see_through'][0] for r in rows), 'see_through_rays': rows[0]['see_through'][1],
               'stretch_body_p99_max': round(max(r['stretch'][0] for r in rows), 3), 'stretch_head_p01_min': round(min(r['stretch'][1] for r in rows), 3), 'stretch_head_p99_max': round(max(r['stretch'][2] for r in rows), 3)}
        for c in edges:
            mn = min(rows, key=lambda r: r['edges'][c][0]); mx = max(rows, key=lambda r: r['edges'][c][1])
            agg['edges'][c] = {'min_mm': round(mn['edges'][c][0], 2), 'min_frame': mn['frame'], 'max_mm': round(mx['edges'][c][1], 2), 'max_frame': mx['frame']}
        keys = sorted({k for r in rows for k in r['pairs']})
        for k in keys:
            vals = [r['pairs'].get(k, 0) for r in rows]; agg['pairs_max'][k] = max(vals); agg['pairs_frames'][k] = sum(v > 0 for v in vals)
        C = [r['c'] for r in rows]
        agg['folded_triangles_max'] = {t: max(c['folded'][t] for c in C) for t in ('body', 'head')}
        agg['folded_frames'] = sum((c['folded']['body'] + c['folded']['head']) > 0 for c in C)
        agg['joint_thickness_min'] = {j: round(min(c['thick'][j] for c in C), 3) for j in C[0]['thick']}
        agg['joint_thickness_min_frame'] = {j: rows[int(np.argmin([c['thick'][j] for c in C]))]['frame'] for j in C[0]['thick']}
        agg['foot_min_z_mm'] = {s_: round(min(c['foot_min_z'][s_] for c in C)*1000, 2) for s_ in ('L', 'R')}
        agg['foot_max_low_z_mm'] = {s_: round(max(c['foot_min_z'][s_] for c in C)*1000, 2) for s_ in ('L', 'R')}
        slide = {}
        for s_ in ('L', 'R'):
            sp = [np.linalg.norm(np.subtract(C[i + 1]['foot_low_xy'][s_], C[i]['foot_low_xy'][s_]))*30.0 for i in range(len(C) - 1)
                  if C[i]['foot_min_z'][s_] < 0.012 and C[i + 1]['foot_min_z'][s_] < 0.012]
            slide[s_] = {'planted_frame_pairs': len(sp), 'mean_m_per_s': round(float(np.mean(sp)), 3) if sp else None, 'max_m_per_s': round(float(np.max(sp)), 3) if sp else None}
        agg['planted_foot_slide'] = slide
        agg['hips_z_range_m'] = [round(min(c['hips_z'] for c in C), 3), round(max(c['hips_z'] for c in C), 3)]
        hx_ = np.array([c['hips_xy'] for c in C]); agg['hips_xy_travel_m'] = round(float(np.linalg.norm(hx_[-1] - hx_[0])), 3)
        R['actions'][act] = agg; print(glb.name, act, json.dumps({'pairs_max': agg['pairs_max'], 'see': agg['see_through_max']}), flush=True)
    return R


if __name__ == '__main__':
    out = Path(sys.argv[1]); res = {'status': hc.STATUS, 'blender': bpy.app.version_string, 'models': {}}
    for g in sys.argv[2:]:
        res['models'][Path(g).name] = run(Path(g))
    hc.write_json(out, res); print('VERIFY_MOTION OK'); hc.finish()
