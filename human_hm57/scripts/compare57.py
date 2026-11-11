"""HM56 -> HM57 (and HM57 LITE) renders for match presentation. Every model is loaded from its EXPORTED GLB into the same
empty scene setup, with identical camera, pose (same action frame), lights, resolution and samples.
Sets: BODY FACE PARTS NECKMOTION MOTION (close review), MATCH (TV camera ~25 m, 12 m high, 85 mm), REPLAY (camera 3.6 m away,
low, 50 mm), PHONE (the match camera rendered at an iPhone landscape size, 844 x 390 points x3, and the player cut out at
1 pt = 3 px), SMALL (player rendered 32 / 48 / 72 / 96 px tall).
Usage: python compare57.py TAG=<glb> [TAG=<glb> ...] [--sets A,B] [--ref <research reference glb>]
The research reference (--ref, or $HM_RESEARCH_REF) is rendered ONLY into renders/RESEARCH_PRIVATE/ (never into COMPARE/,
never into git, never into the public ZIP) and only in the rest pose (it has its own skeleton and motions).
Writes $HM_BUILD/renders/COMPARE/<set>/<TAG>_*.png and qa/render_ledger_compare.json."""
import sys, math, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector
import hm_common as hc, hm_render as hr, hm_glbscene as gs

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
import os
SRC = {a.split('=', 1)[0]: Path(a.split('=', 1)[1]) for a in args if '=' in a and not a.startswith('--')}
SETS = set(args[args.index('--sets') + 1].split(',')) if '--sets' in args else None
REF = Path(args[args.index('--ref') + 1]) if '--ref' in args else (Path(os.environ['HM_RESEARCH_REF']) if os.environ.get('HM_RESEARCH_REF') else None)
if REF is not None:
    SRC['REF'] = REF
OUT_PUBLIC = hc.BUILD/'renders/COMPARE'; OUT_PRIVATE = hc.BUILD/'renders/RESEARCH_PRIVATE'; LEDGER = []


def shoot(sc, cam, target, view, path, src, note, dist=6.0):
    hr.aim(cam, target, view, dist); sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    LEDGER.append({'png': str(Path(path).relative_to(hc.BUILD)), 'png_sha256': hc.sha256(path), 'source': src.name, 'source_sha256': hc.sha256(src), 'view': view if isinstance(view, str) else list(view),
                   'pixels': [sc.render.resolution_x, sc.render.resolution_y], 'samples': sc.cycles.samples, 'note': note})


def persp(sc, cam, target, offset, lens, path, src, note, view):
    cam.data.type = 'PERSP'; cam.data.lens = lens; cam.data.sensor_width = 36
    loc = Vector(target) + Vector(offset); cam.location = loc; cam.rotation_euler = (Vector(target) - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    LEDGER.append({'png': str(Path(path).relative_to(hc.BUILD)), 'png_sha256': hc.sha256(path), 'source': src.name, 'source_sha256': hc.sha256(src), 'view': view, 'pixels': [sc.render.resolution_x, sc.render.resolution_y], 'samples': sc.cycles.samples, 'note': note})
    cam.data.type = 'ORTHO'


def broadcast(sc, cam, target, path, src, note, lens=85):
    """Perspective camera at ~25 m, 12 m high, telephoto (a TV-style match view). Player is about 90 px tall at 1280x720."""
    persp(sc, cam, target, (10.0, -22.0, 12.0), lens, path, src, note, f'broadcast_25m_{lens}mm')


def ground(sc):
    me = bpy.data.meshes.new('Pitch'); me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)]); ob = bpy.data.objects.new('Pitch', me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new('PitchMat'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.10, 0.30, 0.09, 1); b.inputs['Roughness'].default_value = 0.95; me.materials.append(m)
    return ob


ACTION_FRAMES = [('Run', [0, 5, 10, 15]), ('Kick', [8, 14, 19, 25]), ('Header', [9, 17, 21, 30]), ('LookAround', [15, 45, 70, 80]), ('ThrowIn', [0, 13, 20, 29])]
HM_POSE = lambda arm, act, f: gs.pose(arm, None if (act is None or TAG == 'REF') else 'TM_HM55_' + act, f)
for TAG, src in SRC.items():
    tag = TAG; OUT = OUT_PRIVATE if TAG == 'REF' else OUT_PUBLIC
    def want(s):
        if TAG == 'REF' and s not in ('BODY', 'FACE', 'MATCH', 'REPLAY', 'PHONE', 'SMALL'):
            return False
        return SETS is None or s in SETS
    if want('BODY'):
        d = OUT/'BODY'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(420, 840), samples=40, ortho=1.95, target=(0, 0, 0.90))
        for v in ('front', 'quarter_L', 'side_L', 'back'):
            shoot(sc, cam, T, v, d/f'{tag}_{v}.png', src, 'rest pose')
    if want('FACE'):
        d = OUT/'FACE'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(480, 480), samples=48, ortho=0.30, target=(0, 0, 1.665))
        for v in ('front', 'quarter_L', 'side_L', (0.45, -0.85, -0.30)):
            shoot(sc, cam, T, v, d/f'{tag}_{v if isinstance(v, str) else "low"}.png', src, 'rest pose')
    if want('PARTS'):
        d = OUT/'PARTS'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(480, 480), samples=40, ortho=0.62, target=(0, 0, 1.45))
        for lab, tgt, v, o in (('neck_front', (0, 0, 1.50), 'front', 0.55), ('neck_quarter', (0, 0, 1.50), 'quarter_L', 0.55), ('neck_side', (0, 0, 1.50), 'side_L', 0.55), ('neck_back', (0, 0, 1.50), 'back', 0.55),
                               ('legs_front', (0, 0, 0.32), 'front', 0.70), ('legs_side', (0, 0, 0.32), 'side_L', 0.70), ('legs_quarter', (0, 0, 0.32), 'quarter_L', 0.70), ('boot_side', (0.10, -0.03, 0.08), 'side_L', 0.34)):
            cam.data.ortho_scale = o; shoot(sc, cam, tgt, v, d/f'{tag}_{lab}.png', src, 'rest pose close-up')
    if want('NECKMOTION'):
        d = OUT/'NECKMOTION'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(420, 420), samples=40, ortho=0.56, target=(0, 0, 1.56))
        for lab, act, f in (('turn_left', 'LookAround', 15), ('turn_right', 'LookAround', 45), ('look_up', 'LookAround', 70), ('look_down', 'LookAround', 80), ('tilt', 'LookAround', 90), ('header', 'Header', 21), ('throw', 'ThrowIn', 13)):
            HM_POSE(arm, act, f); nk = gs.bone_head(arm, 'Neck'); tgt = (float(nk[0]), float(nk[1]), float(nk[2]) + 0.085)
            for v in ('front', 'side_L', 'back', (0.25, -0.55, 0.80)):
                shoot(sc, cam, tgt, v, d/f'{tag}_{lab}_{v if isinstance(v, str) else "above"}.png', src, f'{act} frame {f}')
        for lab, act, f in (('armpit_kick', 'Kick', 19), ('armpit_throw', 'ThrowIn', 13)):
            HM_POSE(arm, act, f); sh = gs.bone_head(arm, 'UpperArm_L'); cam.data.ortho_scale = 0.50
            for v in ('front', (0.9, 0.2, -0.2)):
                shoot(sc, cam, tuple(float(x) for x in sh), v, d/f'{tag}_{lab}_{v if isinstance(v, str) else "side_low"}.png', src, f'{act} frame {f}')
        for lab, act, f in (('knee_run', 'Run', 5), ('knee_kick', 'Kick', 14), ('knee_header', 'Header', 10)):
            HM_POSE(arm, act, f); kn = gs.bone_head(arm, 'LowerLeg_L'); cam.data.ortho_scale = 0.50
            for v in ('side_L', (0.6, 0.75, 0.1)):
                shoot(sc, cam, tuple(float(x) for x in kn), v, d/f'{tag}_{lab}_{v if isinstance(v, str) else "back_quarter"}.png', src, f'{act} frame {f}')
        cam.data.ortho_scale = 0.56
    if want('MOTION'):
        d = OUT/'MOTION'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(320, 512), samples=24, ortho=2.15, target=(0, 0, 0.95))
        for act, frames in ACTION_FRAMES:
            for f in frames:
                HM_POSE(arm, act, f); hips = gs.bone_head(arm, 'Hips'); tgt = (float(hips[0]), float(hips[1]), 0.98)
                for v in ('quarter_L', 'side_L'):
                    shoot(sc, cam, tgt, v, d/f'{tag}_{act}_{f:03d}_{v}.png', src, f'{act} frame {f}')
    if want('MATCH'):
        d = OUT/'MATCH'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(1280, 720), samples=32, ortho=2.0, target=(0, 0, 0.9)); ground(sc)
        for lab, act, f in (('stand', None, 0), ('run', 'Run', 5), ('kick', 'Kick', 19), ('header', 'Header', 21)):
            if TAG == 'REF' and act is not None:
                continue
            HM_POSE(arm, act, f); broadcast(sc, cam, (0, 0, 0.9), d/f'{tag}_broadcast_{lab}.png', src, f'{lab}; camera 25 m away, 12 m high, 85 mm lens')
    if want('SMALL'):
        d = OUT/'SMALL'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src)
        for px in (32, 48, 72, 96):
            HM_POSE(arm, 'Run', 5); sc2, cam2, T2 = hr.setup(res=(px, px*2), samples=24, ortho=2.0, target=(0, 0, 0.92))
            shoot(sc2, cam2, T2, 'quarter_L', d/f'{tag}_{px}px_run.png', src, 'rendered at this pixel size (player height = image height)')
    if want('REPLAY'):
        d = OUT/'REPLAY'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(960, 540), samples=40, ortho=2.0, target=(0, 0, 0.9)); ground(sc)
        for lab, act, f, off in ((('stand', None, 0, (-2.2, -2.6, 0.55)),) if TAG == 'REF' else (('kick', 'Kick', 19, (-2.2, -2.6, 0.55)), ('header', 'Header', 21, (2.6, -2.4, 0.35)), ('run', 'Run', 5, (-3.0, -1.8, 0.45)), ('throw', 'ThrowIn', 13, (2.4, -2.6, 0.5)))):
            HM_POSE(arm, act, f); hips = gs.bone_head(arm, 'Hips') if TAG != 'REF' else np.array([0, 0, 0.95]); tgt = (float(hips[0]), float(hips[1]), float(hips[2]) + 0.05)
            persp(sc, cam, tgt, off, 50, d/f'{tag}_replay_{lab}.png', src, f'{lab}; replay camera ~3.6 m, 50 mm', 'replay_3.6m_50mm')
    if want('PHONE'):
        d = OUT/'PHONE'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(2532, 1170), samples=24, ortho=2.0, target=(0, 0, 0.9)); ground(sc)
        for lab, act, f in ((('stand', None, 0),) if TAG == 'REF' else (('run', 'Run', 5), ('kick', 'Kick', 19))):
            HM_POSE(arm, act, f)
            persp(sc, cam, (0, 0, 0.9), (10.0, -22.0, 12.0), 50, d/f'{tag}_phone_{lab}.png', src, f'{lab}; iPhone landscape 844x390 pt at 3x, match camera 25 m with a 50 mm lens (wider match view)', 'phone_match_50mm')
hc.write_json(hc.BUILD/'qa/render_ledger_compare.json', {'count': len([r for r in LEDGER if 'RESEARCH_PRIVATE' not in r['png']]), 'renders': [r for r in LEDGER if 'RESEARCH_PRIVATE' not in r['png']]})
if any('RESEARCH_PRIVATE' in r['png'] for r in LEDGER):
    hc.write_json(hc.BUILD/'renders/RESEARCH_PRIVATE/render_ledger_research.json', {'note': 'research reference renders: private review only, never published', 'renders': [r for r in LEDGER if 'RESEARCH_PRIVATE' in r['png']]}); print('COMPARE RENDERS', len(LEDGER)); hc.finish()
