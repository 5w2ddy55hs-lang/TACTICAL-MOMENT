"""Quick preview renders of a face x hair combination (FACE52 review camera/lights).
Usage: python preview.py OUT_PREFIX F0 H1 [size] [samples] [views comma list]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_assemble as asm, fh53_render as rr

a = sys.argv[1:]
prefix, fid, hid = a[0], a[1], a[2]
size = int(a[3]) if len(a) > 3 else 256; samples = int(a[4]) if len(a) > 4 else 8
names = a[5].split(',') if len(a) > 5 else [v[0] for v in rr.VIEWS]
asm.assemble(fid, hid)
scene, cam, target = rr.setup(size, samples)
rr.render_views(scene, cam, target, prefix, [v for v in rr.VIEWS if v[0] in names])
