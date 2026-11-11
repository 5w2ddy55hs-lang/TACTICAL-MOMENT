"""Studio close-ups (FACE52 framings) for face x hair combos. Usage: OUTDIR F0 H0,H1,... [size] [samples]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fh53_assemble as asm, fh53_render as rr
out, fid, hids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
size = int(sys.argv[4]) if len(sys.argv) > 4 else 256; samples = int(sys.argv[5]) if len(sys.argv) > 5 else 16
for hid in hids:
    asm.assemble(fid, hid)
    scene, cam, target = rr.setup(size, samples)
    rr.render_closeups(scene, cam, f'{out}/{fid}_{hid}')
