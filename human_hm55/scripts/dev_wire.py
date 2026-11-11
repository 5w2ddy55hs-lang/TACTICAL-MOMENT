"""Development: clay + wireframe close-ups. Usage: dev_wire.py <out> <name:cx,cy,cz:ortho:view> ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_head as hh, hm_body as hb, hm_render as hr
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
hc.reset_scene()
for part in hb.build_parts():
    v, f, uv = part.mesh(0); hc.new_mesh_object(part.name, v, f, uv)
d = hh.build_mesh_data(hh.P0); hc.new_mesh_object('Head', d['verts'] + hb.HEAD_PIVOT, d['faces'], d['uvs'])
for sg in (1, -1):
    e = hh.ear_data(d['sdf'], sg); hc.new_mesh_object('Ear%d' % sg, e['verts'] + hb.HEAD_PIVOT, e['faces'], e['uvs'])
sc, cam, T = hr.setup(res=(520, 520), samples=16, ortho=0.6, target=(0, 0, 1.0), clay=True)
dark = bpy.data.materials.new('Wire'); dark.use_nodes = True; dark.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.05, 1)
for ob in [o for o in sc.objects if o.type == 'MESH']:
    w = ob.copy(); w.data = ob.data.copy(); sc.collection.objects.link(w); md = w.modifiers.new('w', 'WIREFRAME'); md.thickness = 0.0016; md.use_replace = True
    w.data.materials.clear(); w.data.materials.append(dark)
from PIL import Image
ims = []
for spec in sys.argv[2:]:
    name, c, o, view = spec.split(':'); T = tuple(float(x) for x in c.split(',')); cam.data.ortho_scale = float(o)
    hr.aim(cam, T, view, 5); sc.render.filepath = str(out/f'wire_{name}.png'); bpy.ops.render.render(write_still=True); ims.append(Image.open(sc.render.filepath))
sheet = Image.new('RGB', (520*len(ims), 520)); [sheet.paste(im, (i*520, 0)) for i, im in enumerate(ims)]; sheet.save(out/'wire_sheet.png')
hc.finish()
