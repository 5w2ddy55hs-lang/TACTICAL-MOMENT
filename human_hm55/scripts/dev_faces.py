"""Development: the four face variants without hair (front, quarter, side) at the same camera."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_assemble as ha, hm_render as hr, hm_head as hh, hm_texture as tx, hm_bake as bk
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); ids = sys.argv[2].split(',') if len(sys.argv) > 2 else ['P0', 'P1', 'P2', 'P3']
from PIL import Image
views = ['front', 'quarter_L', 'side_L']; sheet = Image.new('RGB', (420*len(ids), 420*len(views)))
for c, fid in enumerate(ids):
    hc.reset_scene(); hd = ha.head_data(hh.FACES[fid]['P']); rgb, mask, _ = tx.paint_head(hd, tx.FACE_TEX[fid]); head, _ = ha.build_head(data=hd)
    ao = bk.bake_ao(head, {0: 1024}); tx.save_rgb(out/f'head_{fid}.png', tx.bleed(bk.apply_ao(rgb, ao[0], 0.72), mask))
    head.data.materials[0] = hc.simple_material('Head', hc.load_packed_image(out/f'head_{fid}.png', 'Head'))
    sc, cam, T_ = hr.setup(res=(420, 420), samples=32, ortho=0.33, target=(0, 0, 1.660))
    for r, v in enumerate(views):
        hr.aim(cam, T_, v, 6); sc.render.filepath = str(out/f'{fid}_{v}.png'); bpy.ops.render.render(write_still=True); sheet.paste(Image.open(sc.render.filepath), (c*420, r*420))
    print(fid, 'verts', len(hd['verts']), flush=True)
sheet.save(out/'faces_sheet.png'); hc.finish()
