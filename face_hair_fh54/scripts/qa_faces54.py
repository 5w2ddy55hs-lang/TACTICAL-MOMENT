"""FH54 face QA: UV stretch (skin vs ear) and skin-colour continuity across material seams.
Seam continuity: vertices at the same position but in different materials/objects (face TM26 <-> side slot_14,
back-scalp slot_14 <-> slot_02, face <-> back-scalp) are sampled as texture x vertex colour (sRGB) on each side;
the colour step across the seam is reported (mean / p95 / max of |dRGB|/3)."""
import sys, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from PIL import Image
import fh53_common as fc, fh53_assemble as asm


def corner_colours():
    """[(position, object/material, rgb)] for every corner of face + back scalp."""
    cache = {}; rows = []
    for obn in (fc.FACE_OBJ, fc.BACK_OBJ):
        ob = bpy.data.objects[obn]; me = ob.data; uv = me.uv_layers[0].data; col = me.color_attributes['Col']
        for p in me.polygons:
            mat = ob.material_slots[p.material_index].material
            img = next((n.image for n in mat.node_tree.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image), None)
            if img is not None and img.name not in cache:
                cache[img.name] = np.asarray(Image.open(io.BytesIO(img.packed_file.data)).convert('RGB')).astype(float)
            T = cache.get(img.name) if img is not None else None
            for li in p.loop_indices:
                v = me.loops[li].vertex_index; c = np.array(col.data[li].color_srgb[:3])*255
                if T is not None:
                    h, w, _ = T.shape; u, vv = uv[li].uv
                    c = T[int(np.clip((1 - vv % 1)*h, 0, h - 1)), int(np.clip((u % 1)*w, 0, w - 1))]*np.array(col.data[li].color_srgb[:3])
                rows.append((tuple(np.round(np.array(ob.matrix_world @ me.vertices[v].co), 6)), f'{obn}/{mat.name}', c))
    return rows


def seams(rows):
    by = {}
    for pos, key, c in rows:
        if 'slot_15' in key or 'slot_16' in key:          # mouth interior / eyes: natural contrast, not skin seams
            continue
        by.setdefault(pos, {}).setdefault(key, []).append(c)
    steps = []
    for pos, d in by.items():
        if len(d) < 2:
            continue
        means = [np.mean(v, 0) for v in d.values()]
        for i in range(len(means)):
            for j in range(i + 1, len(means)):
                steps.append(np.abs(means[i] - means[j]).mean())
    s = np.array(steps)
    return {'seam_vertices': int(len(s)), 'step_mean': round(float(s.mean()), 2), 'step_p95': round(float(np.percentile(s, 95)), 2), 'step_max': round(float(s.max()), 2)}


def main():
    out = {}
    for fid in ('F0', 'F1', 'F2', 'F3'):
        asm.assemble(fid, 'H0')
        out[fid] = {'material_seam_colour_step_sRGB': seams(corner_colours())}
    # UV stretch, skin vs ear, from the build log arrays
    import build_faces54 as bf
    bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))
    me0 = bpy.data.objects[fc.FACE_OBJ].data; co0 = np.array([v.co[:] for v in me0.vertices])
    ear_f = fc.HeadField._ear_faces([tuple(c) for c in co0], [list(p.vertices) for p in me0.polygons])
    ear_v = {v for i in ear_f for v in me0.polygons[i].vertices}
    for fid in ('F1', 'F2', 'F3'):
        bpy.ops.wm.open_mainfile(filepath=str(asm.module_file('face', fid)))
        me = bpy.data.objects[fc.FACE_OBJ].data; co1 = np.array([v.co[:] for v in me.vertices])
        uv = np.array([d.uv[:] for d in me.uv_layers[0].data]); me.calc_loop_triangles(); res = {'skin': [], 'ear': []}
        for t in me.loop_triangles:
            L = list(t.loops); V = list(t.vertices); U = uv[L]; Bu = np.array([U[1] - U[0], U[2] - U[0]]).T
            if abs(np.linalg.det(Bu)) < 1e-10:
                continue
            inv = np.linalg.inv(Bu)
            s0 = np.linalg.svd(np.array([co0[V[1]] - co0[V[0]], co0[V[2]] - co0[V[0]]]).T @ inv, compute_uv=False)
            s1 = np.linalg.svd(np.array([co1[V[1]] - co1[V[0]], co1[V[2]] - co1[V[0]]]).T @ inv, compute_uv=False)
            res['ear' if set(V) & ear_v else 'skin'].append((s1[0]/s0[0], s1[1]/s0[1]))
        st = {}
        for k, v in res.items():
            a = np.array(v)
            st[k] = {'triangles': len(a), 'stretch_max': round(float(a[:, 0].max()), 3), 'compress_min': round(float(a[:, 1].min()), 3),
                     'p99_stretch': round(float(np.percentile(a[:, 0], 99)), 3), 'over_1.25x_or_under_0.8x': int(((a[:, 0] > 1.25) | (a[:, 1] < 0.8)).sum())}
        out[fid]['uv_stretch_vs_FACE52'] = st
    fc.write_json(fc.BUILD/'qa/qa_faces54.json', out)
    for k, v in out.items():
        print(k, v)


if __name__ == '__main__':
    main()
    fc.finish()
