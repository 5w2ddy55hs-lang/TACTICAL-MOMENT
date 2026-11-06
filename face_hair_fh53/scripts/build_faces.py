"""FH53 face candidates F1-F3: shape edits of the FACE52 face mesh (REF09_Face_Eyes_Mouth).

What changes: vertex positions of the face mesh only (contour, jaw, chin, cheeks, nose, mouth
height; ear-top flare). Topology, UVs, vertex colours, materials and textures are unchanged.
Custom normals are carried through the deformation (n' = J^-T n).
What is frozen (displacement weight 0):
  * within 3 mm of the neck-side open boundary and of the back-scalp seam (attachment unchanged)
  * above z = 0.080 (forehead under the hairline) -> every hair module fits every face
  * in front of the ears above z ~ 0.005 (sideburn zone)
REF14_BackScalp is copied unchanged. Head frame / transforms unchanged.

Usage: python build_faces.py [--only F1,F2,F3]
"""
import sys, math, argparse, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
import fh53_common as fc
from scipy.spatial import cKDTree

MM = 0.001
# (name, centre m, displacement mm, sigma mm, mirror)
FACES = {
    'F1': dict(label='F1_LONG_ANGULAR',
               intent_ja='面長・角ばった顎。下顔面を長く、エラ（顎角）を外下へ張り、頬はこけさせ、鼻筋を通す。大人びた硬質な印象。',
               ear=dict(pin=0.55, drop_mm=3.0),
               handles=[('chin_drop', (0, -.080, -.055), (0, -2.5, -8.5), (22, 20, 16), False),
                        ('lower_face', (0, -.095, -.015), (0, 0, -3.5), (26, 22, 12), False),
                        ('jaw_angle', (.052, -.040, -.030), (5.0, 0, -3.5), (12, 16, 14), True),
                        ('chin_square', (.020, -.080, -.055), (2.5, -1.0, -1.5), (10, 12, 10), True),
                        ('cheek_hollow', (.050, -.085, .002), (-3.2, 1.5, 0), (12, 12, 12), True),
                        ('cheekbone', (.056, -.078, .035), (2.2, -.8, .5), (10, 12, 10), True),
                        ('nose_bridge', (0, -.115, .040), (0, -2.2, 0), (8, 10, 14), False),
                        ('nose_tip', (0, -.123, .018), (0, -1.5, -2.2), (9, 8, 8), False)]),
    'F2': dict(label='F2_ROUND_SOFT',
               intent_ja='丸顔・柔らかい輪郭。顎を短く丸め、頬をふっくら外へ、エラを目立たなくし、鼻を短く小鼻を広げる。若く穏やかな印象。',
               ear=dict(pin=0.55, drop_mm=3.0),
               handles=[('chin_raise', (0, -.080, -.055), (0, 1.5, 5.0), (22, 20, 16), False),
                        ('chin_round', (.020, -.080, -.052), (3.2, -.8, 0), (10, 12, 10), True),
                        ('cheek_full', (.052, -.082, .005), (5.8, -2.2, 0), (14, 14, 14), True),
                        ('jaw_soft', (.052, -.040, -.030), (2.0, 0, 2.2), (12, 16, 14), True),
                        ('mouth_up', (0, -.095, -.012), (0, 0, 2.2), (25, 20, 12), False),
                        ('nose_short', (0, -.123, .018), (0, 1.5, 2.0), (9, 8, 8), False),
                        ('nose_wide', (.010, -.115, .015), (1.8, 0, 0), (6, 8, 6), True)]),
    'F3': dict(label='F3_NARROW_SHARP',
               intent_ja='細面・シャープ。エラと下頬を内へ絞り、尖った顎を前下へ、頬骨を高く、鼻筋を強く出す。精悍で鋭い印象。',
               ear=dict(pin=0.55, drop_mm=3.0),
               handles=[('jaw_narrow', (.052, -.040, -.030), (-6.0, 0, -.8), (12, 16, 14), True),
                        ('lower_cheek_in', (.050, -.075, -.015), (-4.8, 0, 0), (12, 14, 12), True),
                        ('chin_point', (0, -.080, -.055), (0, -3.5, -5.0), (14, 16, 12), False),
                        ('chin_narrow', (.020, -.080, -.050), (-3.5, 0, 0), (10, 12, 10), True),
                        ('cheekbone_high', (.056, -.078, .038), (3.0, -1.5, 1.5), (10, 12, 10), True),
                        ('nose_prominent', (0, -.118, .030), (0, -3.0, 0), (7, 10, 14), False),
                        ('brow', (.028, -.105, .070), (0, -1.4, 0), (14, 8, 6), True)]),
}


def handles_expanded(spec):
    out = []
    for name, c, D, sig, mir in spec['handles']:
        out.append((name, np.array(c), np.array(D)*MM, np.array(sig)*MM))
        if mir:
            out.append((name + '_mirror', np.array(c)*[-1, 1, 1], np.array(D)*[-1, 1, 1]*MM, np.array(sig)*MM))
    return out


class Field:
    def __init__(self, spec, neck_pts, back_pts, ear_vertices, face_co):
        self.h = handles_expanded(spec)
        self.neck = cKDTree(neck_pts); self.back = cKDTree(back_pts)
        self.ear = set(ear_vertices); self.spec = spec

    def mask(self, P):
        z = P[:, 2]; ax = np.abs(P[:, 0]); y = P[:, 1]
        m = 1 - fc.smoothstep(0.060, 0.080, z)                                    # hairline zone frozen
        m *= fc.smoothstep(0.003, 0.018, self.neck.query(P)[0])                   # neck boundary frozen
        m *= fc.smoothstep(0.003, 0.015, self.back.query(P)[0])                   # back-scalp seam frozen
        m *= 1 - fc.smoothstep(0.052, 0.066, ax)*fc.smoothstep(-0.075, -0.055, y)*fc.smoothstep(-0.005, 0.015, z)  # sideburn zone
        return m

    def disp(self, P):
        D = np.zeros_like(P)
        for name, c, d, s in self.h:
            w = np.exp(-0.5*(((P - c)/s)**2).sum(1)); D += w[:, None]*d
        return D*self.mask(P)[:, None]

    def ear_disp(self, P):
        """Pin the upper ear toward the head and round its pointed top (ear islands only)."""
        e = self.spec['ear']; x = P[:, 0]; ax = np.abs(x); z = P[:, 2]
        root = 0.066
        w = fc.smoothstep(0.035, 0.080, z)
        D = np.zeros_like(P)
        D[:, 0] = -np.sign(x)*np.maximum(ax - root, 0)*e['pin']*w
        D[:, 2] = -e['drop_mm']*MM*fc.smoothstep(0.068, 0.084, z)*np.clip((ax - root)/0.02, 0, 1)
        return D


def jacobian_normals(fun, P, N, h=0.0004):
    """Transform normals by the inverse-transpose Jacobian of p -> p + fun(p)."""
    J = np.zeros((len(P), 3, 3))
    for k in range(3):
        e = np.zeros(3); e[k] = h
        J[:, :, k] = (fun(P + e) - fun(P - e))/(2*h)
    J += np.eye(3)[None]
    out = np.einsum('nji,nj->ni', np.linalg.inv(J), N)          # J^-T n
    return out/np.linalg.norm(out, axis=1, keepdims=True)


def build(fid, spec, out):
    bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))
    face = bpy.data.objects[fc.FACE_OBJ]; back = bpy.data.objects[fc.BACK_OBJ]; hair = bpy.data.objects[fc.HAIR_OBJ]
    me = face.data
    co = np.array([v.co[:] for v in me.vertices])
    # ear vertices = vertices of HeadField ear faces
    ear_faces = fc.HeadField._ear_faces([tuple(c) for c in co], [list(p.vertices) for p in me.polygons])
    ear_v = sorted({v for i in ear_faces for v in me.polygons[i].vertices})
    # neck-side open boundary vertices (z < -0.03) of the face mesh
    E = {}
    for p in me.polygons:
        vs = list(p.vertices)
        for a, b in zip(vs, vs[1:] + vs[:1]):
            k = (min(a, b), max(a, b)); E[k] = E.get(k, 0) + 1
    bnd = sorted({v for k, n in E.items() if n == 1 for v in k})
    neck = co[[v for v in bnd if co[v, 2] < -0.03]]
    bco = np.array([v.co[:] for v in back.data.vertices])
    F = Field(spec, neck, bco, ear_v, co)
    isear = np.zeros(len(co), bool); isear[ear_v] = True
    def total(P, ear_mask=None):
        D = F.disp(P)
        if ear_mask is not None:
            D[ear_mask] = F.ear_disp(P[ear_mask])
        return D
    D = F.disp(co); D[isear] = F.ear_disp(co[isear])
    # normals: per-loop evaluated (custom) normals before the edit
    loops_v = np.array([l.vertex_index for l in me.loops])
    n_before = np.array([n.vector[:] for n in me.corner_normals])
    tri_before = [(p.index, np.array(p.normal[:])) for p in me.polygons]
    newco = co + D
    nl = np.empty_like(n_before)
    face_l = ~isear[loops_v]
    nl[face_l] = jacobian_normals(F.disp, co[loops_v[face_l]], n_before[face_l])
    nl[~face_l] = jacobian_normals(F.ear_disp, co[loops_v[~face_l]], n_before[~face_l])
    me.vertices.foreach_set('co', newco.ravel())
    me.normals_split_custom_set([tuple(x) for x in nl])
    me.update()
    flips = sum(1 for (i, n0) in tri_before if np.dot(n0, np.array(me.polygons[i].normal[:])) < 0)
    areas_ratio = []
    for p in me.polygons:
        P0 = co[list(p.vertices)]; P1 = newco[list(p.vertices)]
        a0 = np.linalg.norm(np.cross(P0[1]-P0[0], P0[2]-P0[0])); a1 = np.linalg.norm(np.cross(P1[1]-P1[0], P1[2]-P1[0]))
        if a0 > 1e-12:
            areas_ratio.append(a1/a0)
    mag = np.linalg.norm(D, axis=1)
    # remove FACE52 hair from the face module file
    bpy.data.objects.remove(hair, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for blk in list(coll):
            if blk.users == 0:
                coll.remove(blk)
    me.name = f'TMF53_{spec["label"]}'
    sc = bpy.context.scene
    for k in list(sc.keys()):
        if k != 'cycles':
            del sc[k]
    sc['fh53_role'] = 'FACE candidate module (REF09_Face_Eyes_Mouth + unchanged REF14_BackScalp). FACE52 head frame.'
    sc['fh53_status'] = 'RESEARCH CANDIDATE. Not approved, not production, no rights clearance. Textures are FACE52 (source-derived) and unchanged.'
    sc['fh53_face_id'] = spec['label']
    face['fh53_face_id'] = spec['label']
    name = f'TM_FH53_{spec["label"]}'
    blend = out/'models/face'/(name + '.blend'); glb = blend.with_suffix('.glb')
    fc.save_blend(blend); fc.export_glb(glb)
    neck_moved = float(np.linalg.norm(D[[v for v in bnd if co[v, 2] < -0.03]], axis=1).max())
    seam_idx = cKDTree(bco).query(co)[0] < 1e-5
    return {'face_id': spec['label'], 'intent_ja': spec['intent_ja'],
            'handles_mm': [(n, list(c), list(d), list(s), m) for n, c, d, s, m in spec['handles']], 'ear': spec['ear'],
            'vertices_moved_over_0.05mm': int((mag > 5e-5).sum()), 'vertices_total': len(co),
            'max_displacement_mm': round(float(mag.max())*1000, 3), 'ear_vertices': len(ear_v),
            'max_ear_displacement_mm': round(float(mag[isear].max())*1000, 3),
            'neck_boundary_max_move_mm': round(neck_moved*1000, 6), 'backscalp_shared_vertices_max_move_mm': round(float(mag[seam_idx].max())*1000 if seam_idx.any() else 0.0, 6),
            'max_skin_move_above_z0.080_mm': round(float(mag[(co[:, 2] > 0.080) & ~isear].max())*1000, 6),
            'face_normal_flips': flips, 'min_area_ratio': round(min(areas_ratio), 4), 'max_area_ratio': round(max(areas_ratio), 4),
            'topology_uv_colour_material_changed': False,
            'blend': blend.name, 'glb': glb.name, 'blend_sha256': fc.sha256(blend), 'glb_sha256': fc.sha256(glb)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only', default='F1,F2,F3'); ap.add_argument('--out', default=str(fc.BUILD))
    a = ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out = Path(a.out); inputs = fc.check_inputs()
    log = {'blender': bpy.app.version_string, 'inputs': inputs, 'faces': {}}
    for fid in a.only.split(','):
        t0 = time.time(); r = build(fid, FACES[fid], out); r['seconds'] = round(time.time()-t0, 1)
        log['faces'][fid] = r
        print('BUILT', fid, {k: r[k] for k in ('max_displacement_mm', 'max_ear_displacement_mm', 'neck_boundary_max_move_mm', 'max_skin_move_above_z0.080_mm', 'face_normal_flips', 'min_area_ratio')}, flush=True)
    fc.write_json(out/'qa'/f'build_faces_{"_".join(a.only.split(","))}.json', log)


if __name__ == '__main__':
    main()
    fc.finish()
