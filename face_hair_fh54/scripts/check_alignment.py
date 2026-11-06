"""Re-check of the static FACE52 -> Reference04 correspondence (eyes/mouth) under the documented translation.
Usage: python check_alignment.py FACE52.blend REF04.blend OUT.json   (writes the measured residuals)"""
import sys, bpy, json
import numpy as np
face_blend, ref_blend, out = sys.argv[1], sys.argv[2], sys.argv[3]
T = np.array([0, -0.0393775999546051, 1.59796941280365])
def mat_verts(ob, matname, evaluated=False):
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); m = e.to_mesh()
    else:
        m = ob.data
    idx = [i for i, s in enumerate(ob.material_slots) if s.material and s.material.name == matname]
    vs = set()
    for p in m.polygons:
        if p.material_index in idx: vs.update(p.vertices)
    mw = np.array(ob.matrix_world)
    co = np.array([tuple(m.vertices[i].co) + (1.0,) for i in sorted(vs)])
    co = (mw @ co.T).T[:, :3]
    return np.unique(np.round(co, 9), axis=0)
bpy.ops.wm.open_mainfile(filepath=face_blend)
F = bpy.data.objects['REF09_Face_Eyes_Mouth']
fe = mat_verts(F, 'SOURCE_APPEARANCE04_slot_16'); fm = mat_verts(F, 'SOURCE_APPEARANCE04_slot_15')
face_dims = list(F.dimensions)
bpy.ops.wm.open_mainfile(filepath=ref_blend)
P = bpy.data.objects['REF_SourcePlayer_reference_only']
res = {'blender': bpy.app.version_string, 'translation_tested': T.tolist()}
for ev in (False, True):
    re_ = mat_verts(P, 'SOURCE_APPEARANCE04_slot_16', ev); rm = mat_verts(P, 'SOURCE_APPEARANCE04_slot_15', ev)
    def match(a, b):
        a2 = a + T
        d = np.sqrt(((a2[:, None, :] - b[None, :, :]) ** 2).sum(-1))
        return {'face_unique': len(a), 'ref_unique': len(b), 'max_nearest_residual': float(d.min(1).max()), 'all_matched_1e-6': bool((d.min(1) < 1e-6).all())}
    res['evaluated_armature' if ev else 'rest_mesh'] = {'eyes': match(fe, re_), 'mouth': match(fm, rm)}
res['face_object_dimensions'] = face_dims
res['ref_scene_unit_system'] = bpy.context.scene.unit_settings.system
res['ref_armature_pose_position'] = bpy.data.objects['REF_SourceRig21'].data.pose_position
open(out, 'w').write(json.dumps(res, indent=2)); print(json.dumps(res, indent=2))
