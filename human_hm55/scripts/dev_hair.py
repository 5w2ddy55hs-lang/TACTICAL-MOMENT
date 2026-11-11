"""Development: head P0 with each hair, head close-ups."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_assemble as ha, hm_render as hr, hm_body as hb, hm_head as hh, hm_texture as tx, hm_bake as bk, hm_hair as hx, hm_hair_textures as ht
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); sids = sys.argv[2].split(',') if len(sys.argv) > 2 else ['H1', 'H2', 'H3', 'H4']
ht.make_cap(out/'TMH55_CAP_STRANDS_512.png'); ht.make_cards(out/'TMH55_CARD_STRANDS_512.png'); ht.make_edge(out/'TMH55_EDGE_STRANDS_512x256.png')
hd = ha.head_data(hh.P0); T = dict(tx.TEX0); hrgb, hmask, _ = tx.paint_head(hd, T)
from PIL import Image
views = ['front', 'quarter_L', 'side_L', 'back_quarter', 'back', 'top']; sheet = Image.new('RGB', (360*len(views), 360*len(sids)))
for r, sid in enumerate(sids):
    t0 = time.time(); hc.reset_scene(); head, _ = ha.build_head(data=hd)
    if r == 0:
        ao = bk.bake_ao(head, {0: 1024}); tx.save_rgb(out/'head.png', tx.bleed(bk.apply_ao(hrgb, ao[0], 0.72), hmask))
    head.data.materials[0] = hc.simple_material('Head', hc.load_packed_image(out/'head.png', 'Head'))
    data = hx.build_hair_data(hd, sid); hair = ha.build_hair(data, ha.hair_materials(sid, out))
    print(sid, {k: data['info'][k] for k in ('cap_triangles', 'cards', 'card_triangles', 'edge_triangles', 'cap_vs_head_overlap_pass', 'card_overlap_pass')}, 'sec', round(time.time() - t0, 1), flush=True)
    sc, cam, T_ = hr.setup(res=(360, 360), samples=32, ortho=0.36, target=(0, 0, 1.675))
    for c, v in enumerate(views):
        hr.aim(cam, T_, v, 6); sc.render.filepath = str(out/f'{sid}_{v}.png'); bpy.ops.render.render(write_still=True); sheet.paste(Image.open(sc.render.filepath), (c*360, r*360))
sheet.save(out/'hair_sheet.png'); hc.finish()
