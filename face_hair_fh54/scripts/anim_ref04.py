"""FH54 provisional neck/weight test on the Reference04 body with its EXISTING actions (review copy only).

The FACE52/FH54 head meshes have no bones or weights. In a NEW review file (Reference04 source never written):
  (A) rigid    : head objects parented to bone REF_joint_20 (world transform kept at rest)
  (B) weighted : Armature modifier on the head meshes; each vertex takes the body's weights near the neck,
                 blended to 100% REF_joint_20 above:  w = lerp(nearest body vertex weights, {joint_20: 1},
                 smoothstep(z_local -0.050 .. -0.010))  (head-local z; neck boundary is at z ~ -0.05)
For every action (3 clips; source fps unknown, phase-normalised 61 frames = '1.0 display s' per the source
metadata - meanings/speeds NOT inferred) every 2nd frame: distance from each head neck-boundary vertex to the
evaluated body surface (Reference04 head hidden), and the head bone rotation relative to its parent.
Usage: python anim_ref04.py
"""
import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import fh53_common as fc, fh53_assemble as asm
import review_ref04 as rv

COMBOS = ['F1_H1', 'F0_H0']
HEAD_BONE, NECK_BONE = 'REF_joint_20', 'REF_joint_11'


def neck_boundary(ob):
    me = ob.data; E = {}
    for p in me.polygons:
        vs = list(p.vertices)
        for a, b in zip(vs, vs[1:] + vs[:1]):
            k = (min(a, b), max(a, b)); E[k] = E.get(k, 0) + 1
    return sorted({v for k, n in E.items() if n == 1 for v in k if me.vertices[v].co.z < -0.03})


def body_bvh(body):
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
    mw = body.matrix_world; V = [mw @ v.co for v in me.vertices]; F = [list(p.vertices) for p in me.polygons]
    t = BVHTree.FromPolygons(V, F); ev.to_mesh_clear(); return t


def head_world_points(objs, idx_map):
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for ob in objs:
        ev = ob.evaluated_get(dg); me = ev.to_mesh(); mw = ev.matrix_world
        for i in idx_map.get(ob.name, []):
            pts.append(np.array(mw @ me.vertices[i].co))
        ev.to_mesh_clear()
    return np.array(pts)


def bind_weighted(objs, body, rig):
    """Transfer body weights to the head's lower neck region (rest pose)."""
    bme = body.data; bco = np.array([body.matrix_world @ v.co for v in bme.vertices])
    gname = {g.index: g.name for g in body.vertex_groups}
    from scipy.spatial import cKDTree
    tree = cKDTree(bco)
    for ob in objs:
        for g in list(ob.vertex_groups):
            ob.vertex_groups.remove(g)
        groups = {}
        mw = ob.matrix_world
        for v in ob.data.vertices:
            pw = np.array(mw @ v.co); d, j = tree.query(pw)
            bw = {gname[g.group]: g.weight for g in bme.vertices[j].groups if g.weight > 1e-4}
            s = float(fc.smoothstep(-0.050, -0.010, v.co.z))
            w = {k: val*(1 - s) for k, val in bw.items()}; w[HEAD_BONE] = w.get(HEAD_BONE, 0.0) + s
            tot = sum(w.values()) or 1.0
            for k, val in w.items():
                if val/tot > 1e-4:
                    groups.setdefault(k, []).append((v.index, val/tot))
        for k, items in groups.items():
            g = ob.vertex_groups.new(name=k)
            for i, val in items:
                g.add([i], val, 'REPLACE')
        mod = ob.modifiers.new('FH54_provisional_armature', 'ARMATURE'); mod.object = rig


def bind_rigid(objs, rig):
    bone = rig.data.bones[HEAD_BONE]
    for ob in objs:
        mw = ob.matrix_world.copy()
        ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = HEAD_BONE
        bpy.context.view_layer.update()
        ob.matrix_world = mw


def run(combo, mode):
    bpy.ops.wm.open_mainfile(filepath=str(fc.REF04_BLEND))
    body = bpy.data.objects['REF_SourcePlayer_reference_only']; rig = bpy.data.objects['REF_SourceRig21']
    rv.hide_ref_head(body)
    fid, hid = combo.split('_')
    objs = []
    for kind, mid, names in (('face', fid, [fc.FACE_OBJ, fc.BACK_OBJ]), ('hair', hid, [fc.HAIR_OBJ])):
        with bpy.data.libraries.load(str(asm.module_file(kind, mid)), link=False) as (src, dst):
            dst.objects = list(names)
        for ob in dst.objects:
            bpy.context.scene.collection.objects.link(ob); ob.location = fc.REF04_HEAD_TRANSLATION; objs.append(ob)
    rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    idx = {o.name: neck_boundary(o) for o in objs if o.name.startswith(fc.FACE_OBJ) or o.name.startswith(fc.BACK_OBJ)}
    if mode == 'rigid':
        bind_rigid(objs, rig)
    else:
        bind_weighted(objs, body, rig)
    bpy.context.view_layer.update()
    rest = head_world_points(objs, idx); bt = body_bvh(body)
    rest_gap = [bt.find_nearest(Vector(p))[3] for p in rest]
    rig.data.pose_position = 'POSE'
    out = {'combo': combo, 'mode': mode, 'neck_boundary_vertices': int(len(rest)),
           'rest_gap_mm': {'mean': float(np.mean(rest_gap))*1000, 'max': float(np.max(rest_gap))*1000}, 'actions': {}}
    sc = bpy.context.scene
    for act in bpy.data.actions:
        rig.animation_data.action = act
        for t in rig.animation_data.nla_tracks:
            t.mute = True
        frames = list(range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2)); rows = []
        for f in frames:
            sc.frame_set(f); bpy.context.view_layer.update()
            P = head_world_points(objs, idx); bt = body_bvh(body)
            gaps = np.array([bt.find_nearest(Vector(p))[3] for p in P])
            pb = rig.pose.bones[HEAD_BONE]; par = rig.pose.bones[NECK_BONE]
            rel = (par.matrix.inverted() @ pb.matrix).to_quaternion(); rel0 = (rig.data.bones[NECK_BONE].matrix_local.inverted() @ rig.data.bones[HEAD_BONE].matrix_local).to_quaternion()
            ang = math.degrees((rel0.inverted() @ rel).angle)
            rows.append({'frame': f, 'gap_mean_mm': float(gaps.mean())*1000, 'gap_max_mm': float(gaps.max())*1000, 'head_rot_vs_neck_deg': ang})
        g = np.array([r['gap_max_mm'] for r in rows]); a = np.array([r['head_rot_vs_neck_deg'] for r in rows])
        out['actions'][act.name] = {'frames': len(rows), 'gap_max_mm': float(g.max()), 'gap_max_frame': rows[int(g.argmax())]['frame'],
                                    'gap_mean_mm': float(np.mean([r['gap_mean_mm'] for r in rows])), 'head_rot_vs_neck_deg_max': float(a.max()),
                                    'per_frame': rows}
    # keep a review file for the weighted/rigid binding of the first combo
    if combo == COMBOS[0]:
        sc['fh54_review_status'] = f'PROVISIONAL {mode} binding of the head to REF_joint_20 for neck review only. Not a production join or skinning.'
        p = fc.BUILD/'models/review'/f'TM_FH54_REVIEW_REF04_ANIM_{mode.upper()}_{combo}.blend'; fc.save_blend(p); out['review_blend'] = p.name
    return out, (body, rig, objs)


def main():
    fc.check_inputs(('FACE52_BLEND', 'REF04_BLEND'))
    res = {'blender': bpy.app.version_string, 'scope': __doc__, 'runs': {}}
    for combo in COMBOS:
        for mode in ('rigid', 'weighted'):
            r, _ = run(combo, mode); res['runs'][f'{combo}_{mode}'] = r
            print('ANIM', combo, mode, 'rest max', round(r['rest_gap_mm']['max'], 2), {k: (round(v['gap_max_mm'], 2), round(v['head_rot_vs_neck_deg_max'], 1)) for k, v in r['actions'].items()}, flush=True)
    fc.write_json(fc.BUILD/'qa/anim_ref04.json', res)


if __name__ == '__main__':
    main()
    fc.finish()
