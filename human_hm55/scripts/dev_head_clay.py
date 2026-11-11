"""Development preview: clay render of the head grid (no textures)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_head as hh, hm_render as hr
out = Path(sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
hc.reset_scene(); d = hh.build_mesh_data(hh.P0)
ob = hc.new_mesh_object('HeadClay', d['verts'], d['faces'], d['uvs'])
for sg in (1, -1):
    e = hh.ear_data(d['sdf'], sg); hc.new_mesh_object('Ear%d' % sg, e['verts'], e['faces'], e['uvs'])
print('verts', len(d['verts']), 'faces', len(d['faces']), 'tris', sum(len(f) - 2 for f in d['faces']), 'bbox', d['verts'].min(0).round(4), d['verts'].max(0).round(4))
sc, cam, T = hr.setup(res=(400, 480), samples=24, ortho=0.34, target=(0, 0, 0.03), clay=True)
hr.render(sc, cam, T, ['front', 'quarter_R', 'side_R', 'back_quarter', 'low_front', 'top'], str(out/'head'))
from PIL import Image
ims = [Image.open(out/f'head_{v}.png') for v in ['front', 'quarter_R', 'side_R', 'back_quarter', 'low_front', 'top']]
sheet = Image.new('RGB', (400*6, 480)); [sheet.paste(im, (i*400, 0)) for i, im in enumerate(ims)]; sheet.save(out/'head_sheet.png')
# 2D diagnostics: sagittal profile (x = 0) and frontal silhouette, 2 px / mm, 1 cm grid
from PIL import ImageDraw
f = d['sdf']; W = 520; H = 760; sc_ = 2000.0
def plot(points_fn, name):
    im = Image.new('RGB', (W, H), (250, 250, 250)); dr = ImageDraw.Draw(im)
    for k in range(-13, 14):
        x = W/2 + k*0.01*sc_; dr.line([(x, 0), (x, H)], fill=(225, 225, 225) if k else (150, 150, 150))
    for k in range(-21, 18):
        y = 330 - k*0.01*sc_; dr.line([(0, y), (W, y)], fill=(225, 225, 225) if k else (150, 150, 150))
    a = np.linspace(-0.13, 0.13, W); zz = np.linspace(0.165, -0.215, H); A, Z = np.meshgrid(a, zz)
    v = points_fn(A, Z); ins = v < 0; edge = ins ^ np.roll(ins, 1, 0) | ins ^ np.roll(ins, 1, 1)
    px = np.asarray(im).copy(); px[edge] = (20, 20, 20); Image.fromarray(px).save(out/name)
plot(lambda A, Z: f(np.stack([np.zeros_like(A), A, Z], -1).reshape(-1, 3)).reshape(A.shape), 'profile_sagittal.png')
ys = np.linspace(-0.13, 0.12, 60)
plot(lambda A, Z: np.min([f(np.stack([A, np.full_like(A, y), Z], -1).reshape(-1, 3)).reshape(A.shape) for y in ys], 0), 'profile_frontal.png')
two = Image.new('RGB', (W*2, H)); two.paste(Image.open(out/'profile_sagittal.png'), (0, 0)); two.paste(Image.open(out/'profile_frontal.png'), (W, 0)); two.save(out/'profiles.png')
hc.finish()
