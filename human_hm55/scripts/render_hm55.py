"""HM55 deliverable renders. Every HM55 image is rendered from the EXPORTED player GLB re-imported into an empty
scene (not from the build scene). Own camera / light rig (hm_render), Cycles CPU, seed 0, no denoise.
The research reference (FH54 head on the Reference04 body) is rendered only for the side-by-side balance sheet
and only when FH54_BUILD is set; it is never used as build input.
Writes $HM_BUILD/renders/<set>/*.png and $HM_BUILD/qa/render_ledger_hm55.json."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
import hm_common as hc, hm_render as hr, hm_glbscene as gs

OUT = hc.BUILD/'renders'; PL = hc.BUILD/'models/players'; LEDGER = []
ONLY = set(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
REP = ['P0_H2', 'P1_H1', 'P2_H4', 'P3_H3']
glb = lambda combo, kit='A': PL/f'TM_HM55_PLAYER_{combo}_KIT{kit}.glb'


def shoot(sc, cam, target, view, path, src, setname, note=''):
    hr.aim(cam, target, view, 6); sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    LEDGER.append({'set': setname, 'png': str(Path(path).relative_to(hc.BUILD)), 'png_sha256': hc.sha256(path), 'source': Path(src).name, 'source_sha256': hc.sha256(src), 'view': view if isinstance(view, str) else list(view),
                   'pixels': [sc.render.resolution_x, sc.render.resolution_y], 'samples': sc.cycles.samples, 'renderer': 'Cycles CPU seed 0 no denoise', 'blender': bpy.app.version_string, 'note': note})


def want(name):
    return not ONLY or name in ONLY


def run(name, fn):
    if want(name):
        (OUT/name).mkdir(parents=True, exist_ok=True); fn(OUT/name, name); print('set', name, 'done', len(LEDGER), flush=True)


def rest(d, n):
    for c in REP:
        arm, _ = gs.load_player(glb(c)); sc, cam, T = hr.setup(res=(360, 720), samples=32, ortho=1.95, target=(0, 0, 0.90))
        for v in ('front', 'quarter_L', 'side_L', 'back'):
            shoot(sc, cam, T, v, d/f'{c}_{v}.png', glb(c), n)


def all16(d, n):
    for g in sorted(PL.glob('*_KITA.glb')):
        c = '_'.join(g.stem.split('_')[3:5]); arm, _ = gs.load_player(g); sc, cam, T = hr.setup(res=(270, 300), samples=24, ortho=0.56, target=(0, 0, 1.60))
        shoot(sc, cam, T, 'front', d/f'{c}_front.png', g, n); shoot(sc, cam, T, 'quarter_L', d/f'{c}_quarter_L.png', g, n)


def faces(d, n):
    for f in ('P0', 'P1', 'P2', 'P3'):
        g = glb(f + '_H2'); arm, _ = gs.load_player(g); sc, cam, T = hr.setup(res=(360, 360), samples=40, ortho=0.33, target=(0, 0, 1.665))
        for v in ('front', 'quarter_L', 'side_L'):
            shoot(sc, cam, T, v, d/f'{f}_{v}.png', g, n)


def hairs(d, n):
    for h in ('H1', 'H2', 'H3', 'H4'):
        g = glb('P0_' + h); arm, _ = gs.load_player(g); sc, cam, T = hr.setup(res=(360, 360), samples=40, ortho=0.36, target=(0, 0, 1.68))
        for v in ('front', 'side_L', 'back', 'top'):
            shoot(sc, cam, T, v, d/f'{h}_{v}.png', g, n)
        cam.data.ortho_scale = 0.15
        for lab, tgt, v in (('ear_L', (0.078, 0.0, 1.655), (1, -0.25, 0.1)), ('ear_R', (-0.078, 0.0, 1.655), (-1, -0.25, 0.1)), ('behind_ear_L', (0.07, 0.03, 1.65), (0.75, 0.66, 0.05)), ('nape', (0, 0.09, 1.60), (0, 1, 0.1))):
            shoot(sc, cam, tgt, v, d/f'{h}_{lab}.png', g, n)


def motion(d, n):
    g = glb('P1_H1'); arm, _ = gs.load_player(g); sc, cam, T = hr.setup(res=(300, 480), samples=24, ortho=2.15, target=(0, 0, 0.95))
    for act, frames in (('Run', [0, 5, 10, 15]), ('Kick', [8, 14, 19, 25]), ('ThrowIn', [0, 13, 20, 29]), ('Header', [9, 17, 21, 30])):
        for f in frames:
            gs.pose(arm, 'TM_HM55_' + act, f); hips = gs.bone_head(arm, 'Hips'); tgt = (float(hips[0]), float(hips[1]), 0.98)
            for v in ('quarter_L', 'side_L', 'back_quarter'):
                shoot(sc, cam, tgt, v, d/f'{act}_{f:03d}_{v}.png', g, n, note=f'{act} frame {f} (30 fps)')


def neck(d, n):
    for c in ('P0_H2', 'P2_H4'):
        g = glb(c); arm, _ = gs.load_player(g); sc, cam, T = hr.setup(res=(360, 360), samples=40, ortho=0.56, target=(0, 0, 1.56))
        for lab, act, f in (('rest', None, 0), ('turn_left', 'LookAround', 15), ('turn_right', 'LookAround', 45), ('up', 'LookAround', 70), ('down', 'LookAround', 80), ('tilt', 'LookAround', 90),
                            ('header_strike', 'Header', 21), ('throw_back', 'ThrowIn', 13)):
            gs.pose(arm, None if act is None else 'TM_HM55_' + act, f); nk = gs.bone_head(arm, 'Neck'); tgt = (float(nk[0]), float(nk[1]), float(nk[2]) + 0.085)
            for v in ('front', 'side_L', 'back', (0.25, -0.55, 0.80)):
                vn = v if isinstance(v, str) else 'above'; shoot(sc, cam, tgt, v, d/f'{c}_{lab}_{vn}.png', g, n, note=f'{act or "rest"} frame {f}')


def kits(d, n):
    for c in ('P0_H1', 'P2_H3'):
        arm, _ = gs.load_player(glb(c, 'B')); sc, cam, T = hr.setup(res=(360, 720), samples=32, ortho=1.95, target=(0, 0, 0.90))
        for v in ('front', 'back'):
            shoot(sc, cam, T, v, d/f'{c}_KITB_{v}.png', glb(c, 'B'), n)


def small(d, n):
    for c in REP:
        for px in (64, 96, 128):
            arm, _ = gs.load_player(glb(c)); sc, cam, T = hr.setup(res=(px, px*2), samples=24, ortho=1.95, target=(0, 0, 0.90))
            for v in ('front', 'quarter_L'):
                shoot(sc, cam, T, v, d/f'{c}_{px}px_{v}.png', glb(c), n, note='rendered at this pixel size (not downscaled)')


def reference(d, n):
    fb = os.environ.get('FH54_BUILD')
    if not fb:
        print('reference set skipped: FH54_BUILD not set'); return
    src = Path(fb)/'models/review/TM_FH54_REVIEW_REF04_ANIM_WEIGHTED_F1_H1.blend'; bpy.ops.wm.open_mainfile(filepath=str(src))
    for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA')]:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        if o.type == 'ARMATURE':
            if o.animation_data:
                o.animation_data.action = None
            for pb in o.pose.bones:
                pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update(); sc, cam, T = hr.setup(res=(360, 720), samples=32, ortho=1.95, target=(0, 0, 0.90))
    for v in ('front', 'quarter_L', 'side_L', 'back'):
        shoot(sc, cam, T, v, d/f'RESEARCH_FH54_F1_H1_on_Reference04_{v}.png', src, n, note='research reference, source-derived, comparison only')
    cam.data.ortho_scale = 0.56
    for v in ('front', 'side_L', 'back'):
        shoot(sc, cam, (0, -0.02, 1.56), v, d/f'RESEARCH_neck_{v}.png', src, n, note='research reference, source-derived, comparison only')


for name, fn in (('REST', rest), ('ALL16', all16), ('FACES', faces), ('HAIRS', hairs), ('MOTION', motion), ('NECK', neck), ('KITS', kits), ('SMALL', small), ('REFERENCE', reference)):
    run(name, fn)
led = hc.BUILD/'qa/render_ledger_hm55.json'
if ONLY and led.exists():
    import json
    old = [r for r in json.loads(led.read_text())['renders'] if r['set'] not in ONLY]; LEDGER[:0] = old
hc.write_json(led, {'count': len(LEDGER), 'renders': LEDGER, 'note': 'Static renders of exported GLBs. Not an in-game, device or GPU test.'}); print('RENDERS', len(LEDGER)); hc.finish()
