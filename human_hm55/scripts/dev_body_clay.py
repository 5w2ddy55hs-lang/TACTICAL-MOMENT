"""Development preview: clay render of body parts + head (no textures, no rig)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_head as hh, hm_body as hb, hm_render as hr
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
hc.reset_scene(); tris = 0
for part in hb.build_parts():
    v, f, uv = part.mesh(0); hc.new_mesh_object(part.name, v, f, uv); tris += sum(len(x) - 2 for x in f); print(part.name, 'verts', len(v), 'tris', sum(len(x) - 2 for x in f), 'flip', part.flip)
d = hh.build_mesh_data(hh.P0); hc.new_mesh_object('Head', d['verts'] + hb.HEAD_PIVOT, d['faces'], d['uvs'])
for sg in (1, -1):
    e = hh.ear_data(d['sdf'], sg); hc.new_mesh_object('Ear%d' % sg, e['verts'] + hb.HEAD_PIVOT, e['faces'], e['uvs'])
print('body tris', tris)
views = ['front', 'quarter_R', 'side_R', 'back', 'back_quarter']
sc, cam, T = hr.setup(res=(360, 720), samples=24, ortho=1.95, target=(0, 0, 0.90), clay=True)
hr.render(sc, cam, T, views, str(out/'body'), dist=6)
from PIL import Image
sheet = Image.new('RGB', (360*len(views), 720)); [sheet.paste(Image.open(out/f'body_{v}.png'), (i*360, 0)) for i, v in enumerate(views)]; sheet.save(out/'body_sheet.png')
hc.finish()
