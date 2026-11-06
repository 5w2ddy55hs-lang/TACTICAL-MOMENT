"""Front/quarter face close-ups (512 px) for face module ids with a given hair. Usage: OUTDIR HAIR F0,F1,..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fh53_assemble as asm, fh53_render as rr
out, hid, fids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
size = int(sys.argv[4]) if len(sys.argv) > 4 else 384
SH = [('face_front', (0, -.6, .04), (0, 0, .04), .16), ('face_quarterR', (.42, -.42, .05), (0, 0, .04), .16), ('face_sideR', (.6, 0, .04), (0, 0, .04), .17)]
for fid in fids:
    asm.assemble(fid, hid); sc, cam, tg = rr.setup(size, 16)
    rr.render_closeups(sc, cam, f'{out}/{fid}_{hid}', SH)
