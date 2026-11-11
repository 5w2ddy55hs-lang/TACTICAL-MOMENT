"""HM55 -> HM56 before/after renders. Both models are loaded from their EXPORTED GLBs into the same empty scene setup,
with identical camera, pose (same action frame), lights, resolution and samples.
Usage: python compare56.py <HM55 player glb> <HM56 player glb> [--sets A,B,...]; writes $HM_BUILD/renders/COMPARE/<set>/{HM55,HM56}_*.png
and $HM_BUILD/qa/render_ledger_compare.json."""
import sys, math, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector
import hm_common as hc, hm_render as hr, hm_glbscene as gs

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
SRC = {'HM55': Path(args[0]), 'HM56': Path(args[1])}
SETS = set(args[args.index('--sets') + 1].split(',')) if '--sets' in args else None
OUT = hc.BUILD/'renders/COMPARE'; LEDGER = []


def shoot(sc, cam, target, view, path, src, note, dist=6.0):
    hr.aim(cam, target, view, dist); sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    LEDGER.append({'png': str(Path(path).relative_to(hc.BUILD)), 'png_sha256': hc.sha256(path), 'source': src.name, 'source_sha256': hc.sha256(src), 'view': view if isinstance(view, str) else list(view),
                   'pixels': [sc.render.resolution_x, sc.render.resolution_y], 'samples': sc.cycles.samples, 'note': note})


def broadcast(sc, cam, target, path, src, note):
    """Perspective camera at ~25 m, 12 m high, telephoto (a TV-style match view). Player is about 90 px tall at 1280x720."""
    cam.data.type = 'PERSP'; cam.data.lens = 85; cam.data.sensor_width = 36
    loc = Vector(target) + Vector((10.0, -22.0, 12.0)); cam.location = loc; cam.rotation_euler = (Vector(target) - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    LEDGER.append({'png': str(Path(path).relative_to(hc.BUILD)), 'png_sha256': hc.sha256(path), 'source': src.name, 'source_sha256': hc.sha256(src), 'view': 'broadcast_25m', 'pixels': [sc.render.resolution_x, sc.render.resolution_y], 'samples': sc.cycles.samples, 'note': note})
    cam.data.type = 'ORTHO'


def ground(sc):
    me = bpy.data.meshes.new('Pitch'); me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)]); ob = bpy.data.objects.new('Pitch', me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new('PitchMat'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.10, 0.30, 0.09, 1); b.inputs['Roughness'].default_value = 0.95; me.materials.append(m)
    return ob


ACTION_FRAMES = [('Run', [0, 5, 10, 15]), ('Kick', [8, 14, 19, 25]), ('Header', [9, 17, 21, 30]), ('LookAround', [15, 45, 70, 80]), ('ThrowIn', [0, 13, 20, 29])]
for tag, src in SRC.items():
    def want(s):
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
            gs.pose(arm, 'TM_HM55_' + act, f); nk = gs.bone_head(arm, 'Neck'); tgt = (float(nk[0]), float(nk[1]), float(nk[2]) + 0.085)
            for v in ('front', 'side_L', 'back', (0.25, -0.55, 0.80)):
                shoot(sc, cam, tgt, v, d/f'{tag}_{lab}_{v if isinstance(v, str) else "above"}.png', src, f'{act} frame {f}')
        for lab, act, f in (('armpit_kick', 'Kick', 19), ('armpit_throw', 'ThrowIn', 13)):
            gs.pose(arm, 'TM_HM55_' + act, f); sh = gs.bone_head(arm, 'UpperArm_L'); cam.data.ortho_scale = 0.50
            for v in ('front', (0.9, 0.2, -0.2)):
                shoot(sc, cam, tuple(float(x) for x in sh), v, d/f'{tag}_{lab}_{v if isinstance(v, str) else "side_low"}.png', src, f'{act} frame {f}')
        for lab, act, f in (('knee_run', 'Run', 5), ('knee_kick', 'Kick', 14), ('knee_header', 'Header', 10)):
            gs.pose(arm, 'TM_HM55_' + act, f); kn = gs.bone_head(arm, 'LowerLeg_L'); cam.data.ortho_scale = 0.50
            for v in ('side_L', (0.6, 0.75, 0.1)):
                shoot(sc, cam, tuple(float(x) for x in kn), v, d/f'{tag}_{lab}_{v if isinstance(v, str) else "back_quarter"}.png', src, f'{act} frame {f}')
        cam.data.ortho_scale = 0.56
    if want('MOTION'):
        d = OUT/'MOTION'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(320, 512), samples=24, ortho=2.15, target=(0, 0, 0.95))
        for act, frames in ACTION_FRAMES:
            for f in frames:
                gs.pose(arm, 'TM_HM55_' + act, f); hips = gs.bone_head(arm, 'Hips'); tgt = (float(hips[0]), float(hips[1]), 0.98)
                for v in ('quarter_L', 'side_L'):
                    shoot(sc, cam, tgt, v, d/f'{tag}_{act}_{f:03d}_{v}.png', src, f'{act} frame {f}')
    if want('MATCH'):
        d = OUT/'MATCH'; d.mkdir(parents=True, exist_ok=True); arm, _ = gs.load_player(src); sc, cam, T = hr.setup(res=(1280, 720), samples=32, ortho=2.0, target=(0, 0, 0.9)); ground(sc)
        for lab, act, f in (('stand', None, 0), ('run', 'Run', 5), ('kick', 'Kick', 19)):
            gs.pose(arm, None if act is None else 'TM_HM55_' + act, f); broadcast(sc, cam, (0, 0, 0.9), d/f'{tag}_broadcast_{lab}.png', src, f'{lab}; camera 25 m away, 12 m high, 85 mm lens')
        for px in (48, 72, 96):
            gs.pose(arm, 'TM_HM55_Run', 5); sc2, cam2, T2 = hr.setup(res=(px, px*2), samples=24, ortho=2.0, target=(0, 0, 0.92))
            shoot(sc2, cam2, T2, 'quarter_L', d/f'{tag}_{px}px_run.png', src, 'rendered at this pixel size')
hc.write_json(hc.BUILD/'qa/render_ledger_compare.json', {'count': len(LEDGER), 'renders': LEDGER}); print('COMPARE RENDERS', len(LEDGER)); hc.finish()
