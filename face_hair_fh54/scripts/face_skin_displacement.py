"""Measure per-face skin (non-ear) vertex displacement vs FACE52. Writes build/qa/face_skin_displacement.json."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, bpy
import fh53_common as fc, fh53_assemble as asm
bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))
me = bpy.data.objects[fc.FACE_OBJ].data; co0 = np.array([v.co[:] for v in me.vertices])
ear = fc.HeadField._ear_faces([tuple(c) for c in co0], [list(p.vertices) for p in me.polygons])
ear_v = sorted({v for i in ear for v in me.polygons[i].vertices}); mask = np.ones(len(co0), bool); mask[ear_v] = False
out = {}
for fid in ('F1', 'F2', 'F3'):
    bpy.ops.wm.open_mainfile(filepath=str(asm.module_file('face', fid)))
    co = np.array([v.co[:] for v in bpy.data.objects[fc.FACE_OBJ].data.vertices])
    out[fid] = round(float(np.linalg.norm(co - co0, axis=1)[mask].max())*1000, 3)
fc.write_json(fc.BUILD/'qa/face_skin_displacement.json', out); print(out)
fc.finish()
