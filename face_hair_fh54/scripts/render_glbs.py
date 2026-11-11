"""Render labelled GLBs (imported into empty scenes) with the FACE52 review setup.
Usage: python render_glbs.py OUTDIR MODE LABEL=path.glb [LABEL=path.glb ...]
MODE: seven (7 views 256/8) | studio (close-ups 512/32) | grazing (close-ups 512/32, FACE52 grazing light) | small (front+quarter 64/96/128 px)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_render as rr, fh53_common as fc
out = Path(sys.argv[1]); mode = sys.argv[2]; out.mkdir(parents=True, exist_ok=True)
for item in sys.argv[3:]:
    lab, path = item.split('=', 1)
    def load():
        bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=path)
    if mode == 'seven':
        load(); sc, cam, tg = rr.setup(256, 8); rr.render_views(sc, cam, tg, str(out/lab))
    elif mode in ('studio', 'grazing'):
        load(); sc, cam, tg = rr.setup(512, 32)
        if mode == 'grazing':
            rr.grazing(sc, tg)
        rr.render_closeups(sc, cam, str(out/f'{lab}_{mode}'))
    elif mode == 'small':
        for px in (64, 96, 128):
            load(); sc, cam, tg = rr.setup(px, 16)
            rr.render_views(sc, cam, tg, str(out/f'{lab}_{px}px'), [v for v in rr.VIEWS if v[0] in ('front', 'quarter_R')])
fc.finish()
