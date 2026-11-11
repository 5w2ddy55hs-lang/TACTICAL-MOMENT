"""Development: textured rest-pose character without hair (kit A, head P0)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_assemble as ha, hm_render as hr, hm_body as hb, hm_head as hh, hm_texture as tx, hm_bake as bk
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); tone = 'T2'
hc.reset_scene(); bd = hb.body_data(); hd = ha.head_data(hh.P0)
kit, kmask = tx.paint_kit(bd, 'A'); bskin, smask = tx.paint_body_skin(bd, tone); T = dict(tx.TEX0, tone=tone); hrgb, hmask, _ = tx.paint_head(hd, T)
body, _ = ha.build_body(data=bd); head, _ = ha.build_head(data=hd)
ao_b = bk.bake_ao(body, {0: 1024, 1: 512}); ao_h = bk.bake_ao(head, {0: 1024})
kit = tx.bleed(bk.apply_ao(kit, ao_b[0], 0.70, (1, 1, 1)), kmask); bskin = tx.bleed(bk.apply_ao(bskin, ao_b[1], 0.70), smask); hrgb = tx.bleed(bk.apply_ao(hrgb, ao_h[0], 0.72), hmask)
tx.save_rgb(out/'kit.png', kit); tx.save_rgb(out/'bodyskin.png', bskin); tx.save_rgb(out/'head.png', hrgb)
mk = hc.simple_material('TM_HM55_Kit_A', hc.load_packed_image(out/'kit.png', 'TM_HM55_Kit_A')); ms = hc.simple_material('TM_HM55_BodySkin_' + tone, hc.load_packed_image(out/'bodyskin.png', 'TM_HM55_BodySkin_' + tone))
mh = hc.simple_material('TM_HM55_Head_P0', hc.load_packed_image(out/'head.png', 'TM_HM55_Head_P0'))
body.data.materials[0] = mk; body.data.materials[1] = ms; head.data.materials[0] = mh
arm = ha.build_rig(); ha.bind(body, arm); ha.bind(head, arm)
from PIL import Image
sc, cam, T_ = hr.setup(res=(380, 760), samples=32, ortho=1.95, target=(0, 0, 0.90))
views = ['front', 'quarter_L', 'side_L', 'back']; hr.render(sc, cam, T_, views, str(out/'full'), dist=6)
sheet = Image.new('RGB', (380*4, 760)); [sheet.paste(Image.open(out/f'full_{v}.png'), (i*380, 0)) for i, v in enumerate(views)]; sheet.save(out/'full_sheet.png')
cam.data.ortho_scale = 0.36; sc.render.resolution_x = 440; sc.render.resolution_y = 440; hv = ['front', 'quarter_L', 'side_L', 'back_quarter']
hr.render(sc, cam, (0, 0, 1.655), hv, str(out/'headview'), dist=6)
sheet = Image.new('RGB', (440*4, 440)); [sheet.paste(Image.open(out/f'headview_{v}.png'), (i*440, 0)) for i, v in enumerate(hv)]; sheet.save(out/'head_sheet.png')
hc.save_blend(out/'dev_textured.blend'); hc.finish()
