"""HM57 polygon budget: region-weighted decimation of the generated meshes (Blender Decimate, COLLAPSE, X symmetry).

The meshes are first generated densely from the SDF shapes; then triangles are REMOVED where they do not change the
picture (scalp under the hair, back of the skull, the neck plug hidden in the shirt, skin hidden under sleeves /
shorts / socks) and KEPT where the eye reads a player (face front: eyes, nose, mouth, jaw and chin contour, ears,
hairline; shoulders, elbows, knees, hands, boots). Importance 1 = keep, 0 = free to remove.
Skin weights are interpolated by the collapse and renormalised afterwards; UVs are kept by the collapse.
Run before the Armature modifier is added (the decimation is applied to the rest-pose mesh)."""
import numpy as np
import bpy
import hm_body as hb, hm_head as hh

GROUP = 'HM57_LOD_importance'


def head_importance(P, local):
    """local: head-local vertex positions (N, 3). Returns importance in [0, 1]."""
    q = np.asarray(local, float); az, _, el = hh.azel_of(P, q); line = hh.scalp_line_el(az); z = q[:, 2]
    imp = np.full(len(q), 0.30)
    face = (az < 78) & (el < line + 1.5) & (z > -0.080)
    imp[face] = 1.0
    feat = face & (az < 45) & (z > -0.072) & (z < 0.070)                         # eyes, nose, mouth, chin: always the densest
    imp[feat] = 1.0
    contour = (az >= 60) & (az < 115) & (el < line) & (z > -0.085)               # jaw line and cheek silhouette from the side
    imp[contour] = np.maximum(imp[contour], 0.75)
    hairline = np.abs(el - line) < 5.0                                           # visible edge of the hair
    imp[hairline] = np.maximum(imp[hairline], 0.55)
    scalp = el > line + 5.0                                                      # under the hair cap
    imp[scalp] = 0.04
    neck = z < -0.080
    imp[neck] = np.where(az[neck] < 60, 0.55, 0.35)                              # throat (front) reads more than the nape
    collar = (z < -0.098) & (z > -0.125)                                         # the collar opening must keep its fit
    imp[collar] = 0.70
    hidden = z < -0.135                                                          # plug inside the shirt: may simplify, but must not fold outward
    imp[hidden] = 0.25
    return imp


def body_importance(V, part_of_vertex):
    """V: world rest positions; part_of_vertex: part name per vertex (hm_body part names)."""
    V = np.asarray(V, float); imp = np.full(len(V), 0.45); z = V[:, 2]
    for i, part in enumerate(part_of_vertex):
        p = part or ''
        if p.startswith('torso'):
            imp[i] = 1.0                                                          # shirt: large smooth surface, decimating it showed bumps at match distance -> kept
        elif p.startswith('sleeve'):
            imp[i] = 1.0
        elif p.startswith('arm'):
            imp[i] = 0.75 if z[i] < 1.18 else 0.50                               # forearm, elbow, hand vs the part inside the sleeve (must not poke out)
        elif p.startswith('leg'):
            imp[i] = 0.75 if z[i] < hb.SHORTS_HEM_Z - 0.01 else 0.30             # knee vs the thigh hidden in the shorts
        elif p.startswith('sock'):
            imp[i] = 0.80
        elif p.startswith('boot'):
            imp[i] = 0.65
        elif p.startswith('shorts'):
            imp[i] = 0.50
    return imp


def keep_inside(ob, P, pivot, depth=0.0010):
    """After decimation, collapsed vertices on the scalp / hairline can sit slightly OUTSIDE the dense surface the hair was
    fitted to (quadric placement), and poke through the hair cap. Those vertices are moved back along the SDF gradient
    to `depth` inside the dense head surface. Ears (separate shells outside the skull SDF) are left alone."""
    f = hh.head_sdf(P); V = np.array([v.co for v in ob.data.vertices]) - pivot; az, _, el = hh.azel_of(P, V); line = hh.scalp_line_el(az)
    ear = np.array([0.085, -0.011, 0.035]); near_ear = np.minimum(np.linalg.norm(V - ear, axis=1), np.linalg.norm(V - ear*np.array([-1, 1, 1]), axis=1)) < 0.045
    d0 = f(V); cand = np.where((el > line - 8.0) & (d0 > -depth) & (d0 < 0.006) & ~near_ear)[0]; moved = 0; eps = 1e-4
    for _ in range(8):
        if not len(cand):
            break
        Pq = V[cand]; d = f(Pq); g = np.stack([(f(Pq + e) - f(Pq - e))/(2*eps) for e in np.eye(3)*eps], 1); g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
        V[cand] = Pq - g*(d + depth)[:, None]; moved = max(moved, len(cand)); cand = cand[f(V[cand]) > -depth*0.5]
    for i, v in enumerate(ob.data.vertices):
        v.co = tuple(V[i] + pivot)
    ob.data.update(); return {'moved_inside': int(moved)}


def boundary_vertices(ob):
    """Vertices on open edges (cloth hems, collar, the hidden ends of skin tubes): locked by the decimation so the
    layers keep their spacing."""
    import collections
    cnt = collections.Counter()
    for p in ob.data.polygons:
        for e in p.edge_keys:
            cnt[e] += 1
    return sorted({v for e, c in cnt.items() if c == 1 for v in e})


def tri_count(ob):
    ob.data.calc_loop_triangles(); return len(ob.data.loop_triangles)


def decimate(ob, target_tris, importance, factor=1.0, symmetry=True):
    """Collapse-decimate `ob` to about `target_tris` triangles, protecting vertices by `importance` (per vertex).
    Blender never collapses a vertex whose importance is exactly 1 (inverted group weight 0); scale the map below 1
    (e.g. x0.8 for the mobile LOD) when even the most important areas must be simplified."""
    before = tri_count(ob)
    if target_tris >= before:
        return {'before': before, 'after': before, 'ratio': 1.0}
    g = ob.vertex_groups.new(name=GROUP); imp = np.clip(np.asarray(importance, float), 0, 1)
    for i, w in enumerate(imp):
        g.add([i], float(w), 'REPLACE')
    md = ob.modifiers.new('HM57_LOD', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.vertex_group = GROUP; md.invert_vertex_group = True
    md.vertex_group_factor = factor; md.use_symmetry = symmetry; md.symmetry_axis = 'X'; md.use_collapse_triangulate = True
    ratio = target_tris/before
    for _ in range(6):                                                           # the result is not exactly ratio * before; refine
        md.ratio = ratio; bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); m = ob.evaluated_get(dg).to_mesh()
        m.calc_loop_triangles(); got = len(m.loop_triangles); ob.evaluated_get(dg).to_mesh_clear()
        if abs(got - target_tris) < 0.02*target_tris:
            break
        ratio = float(np.clip(ratio*target_tris/max(got, 1), 0.01, 1.0))
    # take the evaluated result as a new mesh (all data layers: UVs, weights) instead of modifier_apply, which crashed bpy 4.2 intermittently
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    me_new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.remove(md); old = ob.data; ob.data = me_new; bpy.data.meshes.remove(old)
    if GROUP in ob.vertex_groups:
        ob.vertex_groups.remove(ob.vertex_groups[GROUP])
    normalize_weights(ob)
    return {'before': before, 'after': tri_count(ob), 'ratio': round(ratio, 4)}


def normalize_weights(ob, max_influences=4):
    """Keep the strongest `max_influences` bone weights per vertex and make them sum to 1."""
    names = {g.index: g.name for g in ob.vertex_groups}
    for v in ob.data.vertices:
        ws = sorted(((g.weight, g.group) for g in v.groups if g.weight > 1e-5), reverse=True)
        keep = ws[:max_influences]; t = sum(w for w, _ in keep) or 1.0
        for w, gi in ws[max_influences:]:
            ob.vertex_groups[names[gi]].remove([v.index])
        for w, gi in keep:
            ob.vertex_groups[names[gi]].add([v.index], w/t, 'REPLACE')
        for g in list(v.groups):
            if g.weight <= 1e-5:
                ob.vertex_groups[names[g.group]].remove([v.index])
