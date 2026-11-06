"""FH54 face candidates: individual facial features (shape + texture) on the FACE52 face mesh.

For each face F1..F3 three module files are written:
  TM_FH54_<F>_<NAME>.blend/.glb      full candidate  (FH54 shape + FH54 textures)       <- used in the 20 combos
  TM_FH54_<F>S_<NAME>.blend/.glb     shape only      (FH54 shape + FACE52 textures)     <- comparison only
  TM_FH54_<F>T_<NAME>.blend/.glb     texture only    (FACE52 shape + FH54 textures)     <- comparison only
Frozen (displacement weight 0), as in FH53: neck-side open boundary, back-scalp seam, skin above z=0.080
(under every hairline), sideburn zone in front of the ears. REF14_BackScalp geometry is unchanged; only its
textures are replaced (tone-matched) in the textured variants. Topology/UV unchanged; custom normals are
carried through the deformation (n' = J^-T n).
Handle kinds: ('t', centre, disp_mm, sigma_mm, mirror)   translate
              ('s', centre, factors, sigma_mm, mirror)   scale about centre (factors per axis)
              ('r', centre, (axis, deg), sigma_mm, mirror) rotate about centre (mirror flips the angle)
Usage: python build_faces54.py [--only F1,F2,F3]
"""
import sys, math, argparse, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Matrix
import fh53_common as fc
from scipy.spatial import cKDTree

MM = 0.001
EYE_C = (.033, -.093, .056); MOUTH_C = (0, -.098, -.012); NOSE_TIP = (0, -.123, .019)
UPPER_LIP = (0, -.104, -.004); LOWER_LIP = (0, -.100, -.019); MOUTH_CORNER = (.024, -.092, -.014)
CONTOUR = {  # FH53 contour handles (kept; they read well at game size)
    'F1': [('t', (0, -.080, -.055), (0, -2.5, -8.5), (22, 20, 16), False), ('t', (0, -.095, -.015), (0, 0, -3.5), (26, 22, 12), False),
           ('t', (.052, -.040, -.030), (5.0, 0, -3.5), (12, 16, 14), True), ('t', (.020, -.080, -.055), (2.5, -1.0, -1.5), (10, 12, 10), True),
           ('t', (.050, -.085, .002), (-3.2, 1.5, 0), (12, 12, 12), True), ('t', (.056, -.078, .035), (2.2, -.8, .5), (10, 12, 10), True)],
    'F2': [('t', (0, -.080, -.055), (0, 1.5, 5.0), (22, 20, 16), False), ('t', (.020, -.080, -.052), (3.2, -.8, 0), (10, 12, 10), True),
           ('t', (.052, -.082, .005), (4.6, -1.8, 0), (14, 14, 14), True), ('t', (.052, -.040, -.030), (2.0, 0, 2.2), (12, 16, 14), True),
           ('t', (0, -.095, -.012), (0, 0, 2.2), (25, 20, 12), False)],
    'F3': [('t', (.052, -.040, -.030), (-6.0, 0, -.8), (12, 16, 14), True), ('t', (.050, -.075, -.015), (-4.8, 0, 0), (12, 14, 12), True),
           ('t', (0, -.080, -.055), (0, -3.5, -5.0), (14, 16, 12), False), ('t', (.020, -.080, -.050), (-3.5, 0, 0), (10, 12, 10), True),
           ('t', (.056, -.078, .038), (3.0, -1.5, 1.5), (10, 12, 10), True)],
}
FEATURES = {
    'F1': [  # deeper-set, narrower eyes; heavy brow ridge; long straight high nose; wide thin mouth
        ('s', EYE_C, (1.00, 1.0, 0.84), (9, 8, 7), True), ('t', EYE_C, (0, 1.4, 0), (12, 8, 8), True),
        ('t', (.030, -.103, .068), (0, -1.6, .2), (14, 6, 5), True),
        ('t', (0, -.115, .040), (0, -2.0, 0), (8, 10, 14), False), ('t', NOSE_TIP, (0, -1.2, -2.4), (9, 8, 8), False),
        ('s', (0, -.118, .022), (0.92, 1, 1), (10, 8, 10), False),
        ('s', MOUTH_C, (1.08, 1.0, 0.90), (22, 12, 8), False), ('t', UPPER_LIP, (0, .3, -.8), (16, 6, 3), False),
        ('t', LOWER_LIP, (0, .3, .8), (16, 6, 3), False)],
    'F2': [  # larger rounder eyes set wider, outer corners lifted; short round nose; small full mouth
        ('s', EYE_C, (1.07, 1.0, 1.16), (9, 8, 7), True), ('r', EYE_C, ('y', -4.0), (9, 8, 7), True),
        ('t', EYE_C, (.9, -.4, 0), (8, 8, 8), True),
        ('t', NOSE_TIP, (0, 1.5, 2.0), (9, 8, 8), False), ('s', NOSE_TIP, (1.14, 1, 1), (8, 6, 6), False),
        ('s', MOUTH_C, (0.92, 1.0, 1.14), (22, 12, 8), False), ('t', UPPER_LIP, (0, -.6, 1.0), (16, 6, 3), False),
        ('t', LOWER_LIP, (0, -.6, -1.1), (16, 6, 3), False)],
    'F3': [  # almond eyes, lifted outer corners, set closer; narrow high nose; thin upper lip, lifted corners
        ('s', EYE_C, (1.07, 1.0, 0.90), (9, 8, 7), True), ('r', EYE_C, ('y', -6.5), (9, 8, 7), True),
        ('t', EYE_C, (-.7, 0, .2), (8, 8, 8), True),
        ('t', (0, -.118, .030), (0, -3.0, 0), (7, 10, 14), False), ('s', (0, -.115, .022), (0.86, 1, 1), (12, 10, 14), False),
        ('t', UPPER_LIP, (0, .2, -.7), (16, 6, 3), False), ('t', MOUTH_CORNER, (0, 0, .7), (6, 6, 5), True),
        ('t', (.028, -.105, .070), (0, -1.4, 0), (14, 8, 6), True)],
}
LABELS = {'F1': 'F1_LONG_ANGULAR', 'F2': 'F2_ROUND_SOFT', 'F3': 'F3_NARROW_SHARP'}
INTENT = {
    'F1': '面長・角顎の大人顔。目はやや細く深く、眉骨と鼻筋を強く、口は横に広く唇を薄く。日焼けした肌、太い直線眉、薄い髭。',
    'F2': '丸顔の若い柔らかな顔。目を大きく丸く離し目尻をわずかに上げ、鼻は短く丸く、口は小さく唇をふっくら。色白で頬に赤み、柔らかい弓眉、二重の線。',
    'F3': '細面のシャープな顔。切れ長で目尻の上がった目をやや寄せ、鼻は細く高く、上唇は薄く口角を少し上げる。中間の肌色、角度のある眉、頬骨下の陰影、目元の小さなほくろ。',
}
EAR = dict(pin=0.55, drop_mm=3.0, round=0.32)


def rot(axis, deg):
    return np.array(Matrix.Rotation(math.radians(deg), 3, axis.upper()))


def expand(handles):
    out = []
    for kind, c, v, sig, mir in handles:
        c = np.array(c, float); sig = np.array(sig, float)*MM
        out.append((kind, c, v, sig))
        if mir:
            cm = c*[-1, 1, 1]
            if kind == 't':
                out.append((kind, cm, tuple(np.array(v)*[-1, 1, 1]), sig))
            elif kind == 's':
                out.append((kind, cm, v, sig))
            else:
                out.append((kind, cm, (v[0], -v[1]), sig))
    return out


class Field:
    def __init__(self, handles, neck_pts, back_pts):
        self.h = expand(handles); self.neck = cKDTree(neck_pts); self.back = cKDTree(back_pts)

    def mask(self, P):
        z = P[:, 2]; ax = np.abs(P[:, 0]); y = P[:, 1]
        m = 1 - fc.smoothstep(0.060, 0.080, z)
        m *= fc.smoothstep(0.003, 0.018, self.neck.query(P)[0])
        m *= fc.smoothstep(0.003, 0.015, self.back.query(P)[0])
        m *= 1 - fc.smoothstep(0.052, 0.066, ax)*fc.smoothstep(-0.075, -0.055, y)*fc.smoothstep(-0.005, 0.015, z)
        return m

    def disp(self, P):
        D = np.zeros_like(P)
        for kind, c, v, s in self.h:
            w = np.exp(-0.5*(((P - c)/s)**2).sum(1))[:, None]
            if kind == 't':
                D += w*np.array(v)*MM
            elif kind == 's':
                D += w*((P - c)*(np.array(v) - 1))
            else:
                R = rot(*v); D += w*((P - c) @ R.T - (P - c))
        return D*self.mask(P)[:, None]


def ear_field(ear_co):
    """Pin the upper ear toward the head, drop the top, and round the top-back point (per side)."""
    sides = {s: ear_co[np.sign(ear_co[:, 0]) == s] for s in (-1, 1)}
    cen = {s: v.mean(0) for s, v in sides.items() if len(v)}
    def D(P):
        out = np.zeros_like(P); x = P[:, 0]; ax = np.abs(x); z = P[:, 2]; root = 0.066
        w = fc.smoothstep(0.035, 0.080, z)
        out[:, 0] = -np.sign(x)*np.maximum(ax - root, 0)*EAR['pin']*w
        out[:, 2] = -EAR['drop_mm']*MM*fc.smoothstep(0.068, 0.084, z)*np.clip((ax - root)/0.02, 0, 1)
        for s, c in cen.items():
            sel = np.sign(x) == s
            v = P[sel][:, 1:] - c[1:]; r = np.linalg.norm(v, axis=1) + 1e-9
            ang = np.degrees(np.arctan2(v[:, 1], v[:, 0]))                  # 0 = back (+y), 90 = up
            wt = np.exp(-0.5*((ang - 55)/30)**2)*fc.smoothstep(0.006, 0.016, r)
            pull = -(v/r[:, None])*(EAR['round']*np.maximum(r - 0.006, 0)*wt)[:, None]
            out[sel, 1:] += pull
        return out
    return D


def jacobian_normals(fun, P, N, h=0.0004):
    J = np.zeros((len(P), 3, 3))
    for k in range(3):
        e = np.zeros(3); e[k] = h; J[:, :, k] = (fun(P + e) - fun(P - e))/(2*h)
    J += np.eye(3)[None]
    out = np.einsum('nji,nj->ni', np.linalg.inv(J), N)
    return out/np.linalg.norm(out, axis=1, keepdims=True)


def uv_stretch(me, co0, co1):
    """Per-triangle singular values of the UV->3D map, before vs after (texture stretch indicator)."""
    uv = np.array([d.uv[:] for d in me.uv_layers[0].data]); me.calc_loop_triangles(); ratios = []
    for t in me.loop_triangles:
        L = list(t.loops); V = list(t.vertices); U = uv[L]
        Bu = np.array([U[1] - U[0], U[2] - U[0]]).T
        if abs(np.linalg.det(Bu)) < 1e-10:
            continue
        inv = np.linalg.inv(Bu)
        s0 = np.linalg.svd(np.array([co0[V[1]] - co0[V[0]], co0[V[2]] - co0[V[0]]]).T @ inv, compute_uv=False)
        s1 = np.linalg.svd(np.array([co1[V[1]] - co1[V[0]], co1[V[2]] - co1[V[0]]]).T @ inv, compute_uv=False)
        ratios.append((s1[0]/s0[0], s1[1]/s0[1], (s1[0]/s1[1])/(s0[0]/s0[1])))
    r = np.array(ratios)
    return {'triangles': len(r), 'stretch_major_p99': float(np.percentile(r[:, 0], 99)), 'stretch_major_max': float(r[:, 0].max()),
            'stretch_minor_min': float(r[:, 1].min()), 'anisotropy_change_p99': float(np.percentile(r[:, 2], 99)),
            'anisotropy_change_max': float(r[:, 2].max()), 'triangles_over_1.35x': int((r[:, 0] > 1.35).sum() + (r[:, 1] < 1/1.35).sum())}


def assign_textures(fid):
    tex = fc.BUILD/'textures/faces'
    imgs = {k: fc.load_packed_image(tex/f'TMF54_{fid}_{k}.png', f'TMF54_{fid}_{k}') for k in ('FACE', 'SIDE', 'NECK', 'EYE')}
    mapping = {'TM26_Face_Skin_Only': 'FACE', 'SOURCE_APPEARANCE04_slot_14': 'SIDE', 'SOURCE_APPEARANCE04_slot_02': 'NECK', 'SOURCE_APPEARANCE04_slot_16': 'EYE'}
    done = {}
    for m in list(bpy.data.materials):
        if m.name in mapping and m.users:
            nm = m.copy(); nm.name = f'TMF54_{fid}_{m.name}'
            for n in nm.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeTexImage':
                    n.image = imgs[mapping[m.name]]
            nm['fh54_texture'] = f'TMF54_{fid}_{mapping[m.name]}.png (derived from FACE52 texture, see face_textures54.py)'
            for ob in bpy.data.objects:
                for slot in ob.material_slots:
                    if slot.material == m:
                        slot.material = nm
            done[m.name] = nm.name
    # TM27 side skin is vertex-colour only: apply the same tone to its corner colours
    tone = json.loads((fc.BUILD/'qa/face_textures54.json').read_text())['faces'][fid]['params']
    face = bpy.data.objects[fc.FACE_OBJ]; me = face.data; col = me.color_attributes['Col']
    idx = [i for i, s in enumerate(face.material_slots) if s.material and s.material.name.endswith('TM27_Side_Skin_VertexColor')]
    t = np.array(tone['tone']); lift = tone['lift']
    for p in me.polygons:
        if p.material_index in idx:
            for l in p.loop_indices:
                c = np.array(col.data[l].color_srgb[:]); rgb = c[:3]*t; rgb = rgb + lift*(1 - rgb)
                col.data[l].color_srgb = (*rgb, c[3])
    return done


def build(fid, variant, out):
    bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))
    face = bpy.data.objects[fc.FACE_OBJ]; back = bpy.data.objects[fc.BACK_OBJ]; hair = bpy.data.objects[fc.HAIR_OBJ]
    me = face.data; co = np.array([v.co[:] for v in me.vertices])
    ear_faces = fc.HeadField._ear_faces([tuple(c) for c in co], [list(p.vertices) for p in me.polygons])
    ear_v = sorted({v for i in ear_faces for v in me.polygons[i].vertices}); isear = np.zeros(len(co), bool); isear[ear_v] = True
    E = {}
    for p in me.polygons:
        vs = list(p.vertices)
        for a, b in zip(vs, vs[1:] + vs[:1]):
            k = (min(a, b), max(a, b)); E[k] = E.get(k, 0) + 1
    bnd = sorted({v for k, n in E.items() if n == 1 for v in k}); neck_idx = [v for v in bnd if co[v, 2] < -0.03]
    bco = np.array([v.co[:] for v in back.data.vertices])
    info = {'face_id': LABELS[fid], 'variant': variant}
    if variant in ('full', 'shape'):
        F = Field(CONTOUR[fid] + FEATURES[fid], co[neck_idx], bco); EF = ear_field(co[isear])
        D = F.disp(co); D[isear] = EF(co[isear])
        loops_v = np.array([l.vertex_index for l in me.loops]); n0 = np.array([n.vector[:] for n in me.corner_normals])
        nflat0 = {p.index: np.array(p.normal[:]) for p in me.polygons}
        nl = np.empty_like(n0); fl = ~isear[loops_v]
        nl[fl] = jacobian_normals(F.disp, co[loops_v[fl]], n0[fl]); nl[~fl] = jacobian_normals(EF, co[loops_v[~fl]], n0[~fl])
        new = co + D
        # where the surface moved noticeably, blend the transformed FACE52 normals toward the deformed mesh's own
        # smooth normals (position-welded, area-weighted) so deformation does not sharpen existing facets
        key = {}
        for i, c in enumerate(np.round(new, 6)):
            key.setdefault(tuple(c), []).append(i)
        acc = np.zeros_like(new)
        for p_ in me.polygons:
            vs = list(p_.vertices); P = new[vs]
            fn = np.cross(P[1] - P[0], P[2] - P[0])
            for v in vs:
                acc[v] += fn
        welded = np.zeros_like(acc)
        for ids in key.values():
            welded[ids] = acc[ids].sum(0)
        smooth = welded/np.maximum(np.linalg.norm(welded, axis=1, keepdims=True), 1e-12)
        mag_v = np.linalg.norm(D, axis=1)
        alpha = 0.6*fc.smoothstep(0.0003, 0.0025, mag_v[loops_v])*(~isear[loops_v])
        sm_l = smooth[loops_v]; sm_l = np.where((sm_l*nl).sum(1, keepdims=True) < 0, -sm_l, sm_l)
        nl = nl*(1 - alpha[:, None]) + sm_l*alpha[:, None]; nl /= np.linalg.norm(nl, axis=1, keepdims=True)
        info['normal_blend_to_smooth_max_alpha'] = float(alpha.max())
        info['uv_stretch_vs_FACE52'] = uv_stretch(me, co, new)
        me.vertices.foreach_set('co', new.ravel()); me.normals_split_custom_set([tuple(x) for x in nl]); me.update()
        mag = np.linalg.norm(D, axis=1); seam = cKDTree(bco).query(co)[0] < 1e-5
        info.update({'face_normal_flips': int(sum(1 for p in me.polygons if np.dot(nflat0[p.index], np.array(p.normal[:])) < 0)),
                     'max_skin_displacement_mm': round(float(mag[~isear].max())*1000, 3), 'max_ear_displacement_mm': round(float(mag[isear].max())*1000, 3),
                     'neck_boundary_max_move_mm': round(float(mag[neck_idx].max())*1000, 6),
                     'backscalp_shared_vertices_max_move_mm': round(float(mag[seam].max())*1000, 6) if seam.any() else 0.0,
                     'max_skin_move_above_z0.080_mm': round(float(mag[(co[:, 2] > 0.080) & ~isear].max())*1000, 6),
                     'handles': [list(map(str, h)) for h in CONTOUR[fid] + FEATURES[fid]], 'ear': EAR})
    if variant in ('full', 'texture'):
        info['materials_retextured'] = assign_textures(fid)
    bpy.data.objects.remove(hair, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for blk in list(coll):
            if blk.users == 0:
                coll.remove(blk)
    suffix = {'full': '', 'shape': 'S', 'texture': 'T'}[variant]
    me.name = f'TMF54_{fid}{suffix}'
    sc = bpy.context.scene
    for k in list(sc.keys()):
        if k != 'cycles':
            del sc[k]
    sc['fh54_role'] = 'FACE module (REF09_Face_Eyes_Mouth + REF14_BackScalp, back-scalp geometry unchanged). FACE52 head frame.'
    sc['fh54_status'] = 'RESEARCH CANDIDATE. Not approved, no rights clearance. Textures derived from FACE52 (source-derived).'
    sc['fh54_face_id'] = LABELS[fid] + ({'full': '', 'shape': ' (shape only)', 'texture': ' (texture only)'}[variant])
    name = f'TM_FH54_{fid}{suffix}_{LABELS[fid][3:]}'
    blend = out/'models/face'/(name + '.blend'); glb = blend.with_suffix('.glb')
    fc.save_blend(blend); fc.export_glb(glb)
    info.update({'intent_ja': INTENT[fid], 'blend': blend.name, 'glb': glb.name, 'blend_sha256': fc.sha256(blend), 'glb_sha256': fc.sha256(glb)})
    return info


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only', default='F1,F2,F3'); ap.add_argument('--variants', default='full,shape,texture')
    a = ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out = fc.BUILD; log = {'blender': bpy.app.version_string, 'inputs': fc.check_inputs(), 'faces': {}}
    for fid in a.only.split(','):
        for var in a.variants.split(','):
            r = build(fid, var, out); log['faces'][f'{fid}_{var}'] = r
            print('BUILT', fid, var, {k: r.get(k) for k in ('max_skin_displacement_mm', 'neck_boundary_max_move_mm', 'max_skin_move_above_z0.080_mm', 'face_normal_flips')}, flush=True)
    fc.write_json(out/'qa'/'build_faces54.json', log)


if __name__ == '__main__':
    main()
    fc.finish()
