"""Development: HM56 head P0 (clay and textured), front / quarter / side / low close-ups."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_assemble as ha, hm_render as hr, hm_head as hh, hm_texture as tx, hm_bake as bk
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); clay = 'clay' in sys.argv
from PIL import Image
hc.reset_scene(); hd = ha.head_data(hh.P0); head, _ = ha.build_head(data=hd)
print('head verts', len(hd['verts']), 'tris', sum(len(f) - 2 for f in hd['faces']), flush=True)
if not clay:
    rgb, mask, r = tx.paint_head(hd, tx.FACE_TEX['P0']); ao = bk.bake_ao(head, {0: 1024})
    tx.save_rgb(out/'head.png', tx.bleed(bk.apply_ao(rgb, ao[0], 0.45, mask=mask, blur=2.5, limit=np.where(r['fid'] > 0, 0.28, 1.0)), mask))
    head.data.materials[0] = hc.simple_material('Head', hc.load_packed_image(out/'head.png', 'Head'))
sc, cam, T = hr.setup(res=(400, 400), samples=32, ortho=0.30, target=(0, 0, 1.64), clay=clay)
views = ['front', 'quarter_L', 'side_L', (0.35, -0.9, -0.25)]; sheet = Image.new('RGB', (400*len(views), 400))
for i, v in enumerate(views):
    hr.aim(cam, T, v, 6); sc.render.filepath = str(out/f'v{i}.png'); bpy.ops.render.render(write_still=True); sheet.paste(Image.open(sc.render.filepath), (i*400, 0))
sheet.save(out/('sheet_clay.png' if clay else 'sheet.png')); hc.finish()
