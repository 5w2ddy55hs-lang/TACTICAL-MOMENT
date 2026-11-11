"""Continuous playback for match presentation, rendered frame by frame from the EXPORTED GLBs (same camera / light / frames
for every model) and joined into MP4 (H.264, yuv420p, faststart - plays on iPhone) and a GIF:
  HM57_motion_full.mp4     Run (2 loops), Kick, Header, ThrowIn - full body, columns HM56 | HM57 | HM57 LITE
  HM57_closeups.mp4        neck in LookAround, knee in Kick, armpit in ThrowIn - same columns
  HM57_match_replay.mp4    match camera (25 m, 12 m high, 85 mm, following the hips) for Run x2 / Kick / Header, then a replay
                           camera (3.6 m, 50 mm) in half-speed slow motion (sub-frame sampling) for Kick and Header;
                           rows HM57 (top) and HM57 LITE (bottom), portrait for a phone
  HM57_run.gif
Usage: python anim_video57.py <HM56 glb> <HM57 glb> <HM57 LITE glb>; writes $HM_BUILD/video/ and qa/anim_video57.json."""
import sys, os, subprocess, shutil, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont
import hm_common as hc, hm_render as hr, hm_glbscene as gs

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
SRC = {'HM56': Path(args[0]), 'HM57': Path(args[1]), 'HM57L': Path(args[2])}
NAME = {'HM56': 'HM56（改善前）', 'HM57': 'HM57（今回）', 'HM57L': 'HM57 軽量版'}
V = hc.BUILD/'video'; FR = V/'frames'; FR.mkdir(parents=True, exist_ok=True)
FONT = next((f for f in ('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',) if os.path.exists(f)), None)
font = lambda n: ImageFont.truetype(FONT, n) if FONT else ImageFont.load_default()
FULL = [('Run', 2, 'quarter_L'), ('Kick', 1, 'quarter_L'), ('Header', 1, 'side_L'), ('ThrowIn', 1, 'side_L')]
CLOSE = [('neck', 'LookAround', 'front', 0.62, 'Neck'), ('knee', 'Kick', (0.75, 0.55, 0.1), 0.70, 'LowerLeg_L'), ('armpit', 'ThrowIn', (0.9, 0.2, -0.2), 0.62, 'UpperArm_L')]
rec = {'fps': 30, 'models': {k: {'glb': v.name, 'sha256': hc.sha256(v)} for k, v in SRC.items()}, 'clips': []}


def frames_of(act, loops):
    a = next(x for x in bpy.data.actions if x.name.startswith('TM_HM55_' + act)); f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1]))
    return [f for _ in range(loops) for f in range(f0, f1 + (0 if loops > 1 else 1))], (f0, f1)


def ground(sc):
    me = bpy.data.meshes.new('Pitch'); me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)]); ob = bpy.data.objects.new('Pitch', me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new('PitchMat'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.10, 0.30, 0.09, 1); b.inputs['Roughness'].default_value = 0.95; me.materials.append(m)


def persp(cam, target, offset, lens):
    cam.data.type = 'PERSP'; cam.data.lens = lens; cam.data.sensor_width = 36; loc = Vector(target) + Vector(offset); cam.location = loc
    cam.rotation_euler = (Vector(target) - loc).to_track_quat('-Z', 'Y').to_euler()


for tag, src in SRC.items():
    arm, _ = gs.load_player(src)
    # ---- full body (orthographic, follows the hips)
    for act, loops, view in FULL:
        sc, cam, T = hr.setup(res=(300, 450), samples=10, ortho=2.15, target=(0, 0, 0.95)); fr, (f0, f1) = frames_of(act, loops); d = FR/f'full_{act}_{tag}'; d.mkdir(exist_ok=True)
        for k, f in enumerate(fr):
            gs.pose(arm, 'TM_HM55_' + act, f); h = gs.bone_head(arm, 'Hips'); hr.aim(cam, (float(h[0]), float(h[1]), 0.98), view, 6)
            sc.render.filepath = str(d/f'{k:04d}.png'); bpy.ops.render.render(write_still=True)
        if tag == 'HM56':
            rec['clips'].append({'video': 'HM57_motion_full.mp4', 'action': act, 'frames': len(fr), 'source_frames': [f0, f1], 'loops': loops, 'view': view})
        print('frames', tag, act, len(fr), flush=True)
    # ---- close-ups
    for kind, act, view, ortho, track in CLOSE:
        sc, cam, T = hr.setup(res=(300, 300), samples=12, ortho=ortho, target=(0, 0, 1.4)); fr, (f0, f1) = frames_of(act, 1); d = FR/f'close_{kind}_{tag}'; d.mkdir(exist_ok=True)
        for k, f in enumerate(fr):
            gs.pose(arm, 'TM_HM55_' + act, f); b = gs.bone_head(arm, track); hr.aim(cam, (float(b[0]), float(b[1]), float(b[2]) + (0.08 if track == 'Neck' else 0.0)), view, 6)
            sc.render.filepath = str(d/f'{k:04d}.png'); bpy.ops.render.render(write_still=True)
        if tag == 'HM56':
            rec['clips'].append({'video': 'HM57_closeups.mp4', 'action': act, 'part': kind, 'frames': len(fr), 'source_frames': [f0, f1], 'view': view if isinstance(view, str) else list(view)})
    # ---- match camera + slow-motion replay (HM57 and LITE only)
    if tag != 'HM56':
        sc, cam, T = hr.setup(res=(640, 360), samples=12, ortho=2.0, target=(0, 0, 0.9)); ground(sc); seq = []
        for act, loops in (('Run', 2), ('Kick', 1), ('Header', 1)):
            fr, _ = frames_of(act, loops); seq += [('match', act, float(f)) for f in fr]
        for act in ('Kick', 'Header'):
            fr, (f0, f1) = frames_of(act, 1); seq += [('replay', act, f0 + 0.5*i) for i in range(int((f1 - f0)*2) + 1)]
        d = FR/f'matchreplay_{tag}'; d.mkdir(exist_ok=True)
        for k, (cam_kind, act, f) in enumerate(seq):
            a = next(x for x in bpy.data.actions if x.name.startswith('TM_HM55_' + act)); arm.animation_data_create(); arm.animation_data.action = a
            sc.frame_set(int(f), subframe=f - int(f)); bpy.context.view_layer.update(); h = gs.bone_head(arm, 'Hips'); tgt = (float(h[0]), float(h[1]), float(h[2]) + 0.05)
            if cam_kind == 'match':
                persp(cam, (float(h[0]), float(h[1]), 0.9), (10.0, -22.0, 12.0), 85)
            else:
                persp(cam, tgt, (-2.2, -2.6, 0.55) if act == 'Kick' else (2.6, -2.4, 0.35), 50)
            sc.render.filepath = str(d/f'{k:04d}.png'); bpy.ops.render.render(write_still=True)
        if tag == 'HM57':
            rec['match_replay'] = {'frames': len(seq), 'match_camera': '25 m away, 12 m high, 85 mm, following the hips; Run x2, Kick, Header at normal speed',
                                   'replay_camera': '3.6 m, 50 mm; Kick and Header at half speed (animation sampled every 0.5 frame)'}
        print('match/replay', tag, len(seq), flush=True)


def label(img, text, sub=None):
    W, H = img.size; J = Image.new('RGB', (W, H + 30), (20, 24, 32)); J.paste(img, (0, 30)); dr = ImageDraw.Draw(J); dr.text((6, 5), text, fill=(235, 235, 225), font=font(17))
    if sub:
        dr.text((W - 8 - 8*len(sub), 8), sub, fill=(170, 178, 192), font=font(13))
    return J


def join_cols(dirs, out, n, sub):
    out.mkdir(exist_ok=True)
    for k in range(n):
        cols = [label(Image.open(d/f'{k:04d}.png').convert('RGB'), NAME[t], sub(k) if t == 'HM57L' else None) for t, d in dirs]; W, H = cols[0].size
        J = Image.new('RGB', (W*len(cols) + 4*(len(cols) - 1), H), (20, 24, 32))
        for i, c in enumerate(cols):
            J.paste(c, (i*(W + 4), 0))
        J.save(out/f'{k:04d}.png')
    return out


ff = shutil.which('ffmpeg')


def mp4(dirs, out, w, h):
    tmp = []
    for i, dj in enumerate(dirs):
        t = V/f'_part{i}.mp4'; subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(dj/'%04d.png'), '-vf', f'scale=trunc(iw/2)*2:trunc(ih/2)*2,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x141820',
                                               '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-profile:v', 'main', '-crf', '20', str(t)], check=True); tmp.append(t)
    lst = V/'_list.txt'; lst.write_text(''.join(f"file '{t}'\n" for t in tmp))
    subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', '-movflags', '+faststart', str(out)], check=True)
    for t in tmp:
        t.unlink()
    lst.unlink()


tags = list(SRC)
full = [join_cols([(t, FR/f'full_{a}_{t}') for t in tags], FR/f'full_{a}_JOIN', len(list((FR/f'full_{a}_HM56').glob('*.png'))), lambda k, a=a: f'{a} {k + 1}') for a, _, _ in FULL]
close = [join_cols([(t, FR/f'close_{c}_{t}') for t in tags], FR/f'close_{c}_JOIN', len(list((FR/f'close_{c}_HM56').glob('*.png'))), lambda k, c=c: f'{c} {k + 1}') for c, _, _, _, _ in CLOSE]
mp4(full, V/'HM57_motion_full.mp4', 908, 480); mp4(close, V/'HM57_closeups.mp4', 908, 330)
# match / replay: rows HM57 over LITE
dj = FR/'matchreplay_JOIN'; dj.mkdir(exist_ok=True); n = len(list((FR/'matchreplay_HM57').glob('*.png'))); nm = rec['match_replay']['frames']
n_match = sum(1 for _ in range(0))
for k in range(n):
    a = label(Image.open(FR/f'matchreplay_HM57/{k:04d}.png').convert('RGB'), NAME['HM57']); b = label(Image.open(FR/f'matchreplay_HM57L/{k:04d}.png').convert('RGB'), NAME['HM57L'])
    J = Image.new('RGB', (a.size[0], a.size[1]*2 + 4), (20, 24, 32)); J.paste(a, (0, 0)); J.paste(b, (0, a.size[1] + 4)); J.save(dj/f'{k:04d}.png')
mp4([dj], V/'HM57_match_replay.mp4', 640, 784)
subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(FR/'full_Run_JOIN/%04d.png'), '-vf', 'fps=15,scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse', str(V/'HM57_run.gif')], check=True)
for p in sorted(V.glob('HM57_*.mp4')) + sorted(V.glob('HM57_*.gif')):
    rec.setdefault('outputs', {})[p.name] = {'bytes': p.stat().st_size, 'sha256': hc.sha256(p)}
    if p.suffix == '.mp4':
        rec['outputs'][p.name]['ffprobe'] = json.loads(subprocess.run([shutil.which('ffprobe'), '-v', 'error', '-show_entries', 'stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,nb_frames', '-of', 'json', str(p)], capture_output=True, text=True).stdout)
hc.write_json(hc.BUILD/'qa/anim_video57.json', rec); print('VIDEO OK', list(rec['outputs'])); hc.finish()
