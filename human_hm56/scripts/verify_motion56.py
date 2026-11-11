"""Model-agnostic motion verification of an exported player GLB (works the same on HM55 and HM56).
For EVERY frame of every action:
  - open cloth edges (collar, sleeve hems, shirt hem, shorts hems, sock tops, boot tops) are found from the mesh
    itself (boundary loops of the kit material at rest) and their distance to the skin is measured
    (min = how close the hem comes to / into the skin, max = widest opening);
  - skin x cloth triangle intersections, split by region (neck x shirt, arm x shirt/sleeve, knee/thigh x sock, ...);
  - see-through rays into the collar opening;
  - edge stretch of the skinned meshes.
Usage: python verify_motion56.py <out.json> <player.glb> [<player.glb> ...]"""
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
    R = {'glb': glb.name, 'sha256': hc.sha256(glb), 'edge_vertices': {c: len(v) for c, v in edges.items()}, 'rest': metrics(), 'actions': {}}
    for act in ACTIONS:
        a = next(x for x in bpy.data.actions if x.name.startswith('TM_HM55_' + act)); f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1])); rows = []
        for f in range(f0, f1 + 1):
            gs.pose(arm, 'TM_HM55_' + act, f); m = metrics(); m['frame'] = f; rows.append(m)
        agg = {'frames': [f0, f1], 'n_frames': len(rows), 'edges': {}, 'pairs_max': {}, 'pairs_frames': {}, 'see_through_max': max(r['see_through'][0] for r in rows), 'see_through_rays': rows[0]['see_through'][1],
               'stretch_body_p99_max': round(max(r['stretch'][0] for r in rows), 3), 'stretch_head_p01_min': round(min(r['stretch'][1] for r in rows), 3), 'stretch_head_p99_max': round(max(r['stretch'][2] for r in rows), 3)}
        for c in edges:
            mn = min(rows, key=lambda r: r['edges'][c][0]); mx = max(rows, key=lambda r: r['edges'][c][1])
            agg['edges'][c] = {'min_mm': round(mn['edges'][c][0], 2), 'min_frame': mn['frame'], 'max_mm': round(mx['edges'][c][1], 2), 'max_frame': mx['frame']}
        keys = sorted({k for r in rows for k in r['pairs']})
        for k in keys:
            vals = [r['pairs'].get(k, 0) for r in rows]; agg['pairs_max'][k] = max(vals); agg['pairs_frames'][k] = sum(v > 0 for v in vals)
        R['actions'][act] = agg; print(glb.name, act, json.dumps({'pairs_max': agg['pairs_max'], 'see': agg['see_through_max']}), flush=True)
    return R


if __name__ == '__main__':
    out = Path(sys.argv[1]); res = {'status': hc.STATUS, 'blender': bpy.app.version_string, 'models': {}}
    for g in sys.argv[2:]:
        res['models'][Path(g).name] = run(Path(g))
    hc.write_json(out, res); print('VERIFY_MOTION OK'); hc.finish()
