"""Continuous playback of the six motions for HM55 and HM56 (exported GLBs, same camera / light / frames), rendered
frame by frame at 30 fps and joined side by side into MP4 (H.264, yuv420p - plays on iPhone) and a small GIF.
Usage: python anim_video56.py <HM55 glb> <HM56 glb>; writes $HM_BUILD/video/*.mp4|gif and qa/anim_video56.json."""
import sys, os, subprocess, shutil, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
from PIL import Image, ImageDraw, ImageFont
import hm_common as hc, hm_render as hr, hm_glbscene as gs

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
SRC = {'HM55': Path(args[0]), 'HM56': Path(args[1])}; V = hc.BUILD/'video'; FR = V/'frames'; FR.mkdir(parents=True, exist_ok=True)
FONT = next((f for f in ('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',) if os.path.exists(f)), None)
font = lambda n: ImageFont.truetype(FONT, n) if FONT else ImageFont.load_default()
CLIPS = [('full', 'Run', 2, 'quarter_L', 2.10, None, (360, 540)), ('full', 'Kick', 1, 'quarter_L', 2.10, None, (360, 540)), ('full', 'Header', 1, 'side_L', 2.30, None, (360, 540)),
         ('full', 'ThrowIn', 1, 'side_L', 2.30, None, (360, 540)), ('neck', 'LookAround', 1, 'front', 0.62, 'Neck', (360, 360)), ('knee', 'Kick', 1, (0.75, 0.55, 0.1), 0.70, 'LowerLeg_L', (360, 360))]
rec = {'fps': 30, 'clips': []}
for tag, src in SRC.items():
    arm, _ = gs.load_player(src)
    for kind, act, loops, view, ortho, track, res in CLIPS:
        sc, cam, T = hr.setup(res=res, samples=10, ortho=ortho, target=(0, 0, 0.95)); a = next(x for x in bpy.data.actions if x.name.startswith('TM_HM55_' + act)); f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1]))
        frames = [f for _ in range(loops) for f in range(f0, f1 + (0 if loops > 1 else 1))]; d = FR/f'{kind}_{act}_{tag}'; d.mkdir(exist_ok=True)
        for k, f in enumerate(frames):
            gs.pose(arm, 'TM_HM55_' + act, f)
            if track:
                b = gs.bone_head(arm, track); tgt = (float(b[0]), float(b[1]), float(b[2]) + (0.08 if track == 'Neck' else 0.0))
            else:
                h = gs.bone_head(arm, 'Hips'); tgt = (float(h[0]), float(h[1]), 0.98)
            hr.aim(cam, tgt, view, 6); sc.render.filepath = str(d/f'{k:04d}.png'); bpy.ops.render.render(write_still=True)
        print('frames', tag, kind, act, len(frames), flush=True)
        if tag == 'HM55':
            rec['clips'].append({'kind': kind, 'action': act, 'frames': len(frames), 'source_frames': [f0, f1], 'loops': loops, 'view': view if isinstance(view, str) else list(view)})
# join HM55 | HM56 with labels
outs = []
for c in rec['clips']:
    kind, act = c['kind'], c['action']; da, db = FR/f'{kind}_{act}_HM55', FR/f'{kind}_{act}_HM56'; dj = FR/f'{kind}_{act}_JOIN'; dj.mkdir(exist_ok=True)
    for k in range(c['frames']):
        A = Image.open(da/f'{k:04d}.png').convert('RGB'); B = Image.open(db/f'{k:04d}.png').convert('RGB'); W, H = A.size; J = Image.new('RGB', (W*2 + 6, H + 34), (20, 24, 32)); J.paste(A, (0, 34)); J.paste(B, (W + 6, 34))
        dr = ImageDraw.Draw(J); dr.text((8, 6), 'HM55（改良前）', fill=(235, 235, 225), font=font(18)); dr.text((W + 14, 6), 'HM56（改良後）', fill=(235, 235, 225), font=font(18))
        dr.text((W*2 - 150, 8), f'{act} {k + 1}/{c["frames"]}', fill=(190, 196, 210), font=font(14)); J.save(dj/f'{k:04d}.png')
    outs.append(dj)
ff = shutil.which('ffmpeg'); lists = V/'concat.txt'
with open(lists, 'w') as fh:
    for dj in outs:
        if '_full_' in f'_{dj.name}_' or dj.name.startswith('full_'):
            fh.write(f"file '{dj}/%04d.png'\n")
def mp4(dirs, out):
    tmp = []
    for i, dj in enumerate(dirs):
        t = V/f'_part{i}.mp4'; subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(dj/'%04d.png'), '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2,pad=726:574:(ow-iw)/2:(oh-ih)/2:color=0x141820', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-profile:v', 'main', '-crf', '20', str(t)], check=True); tmp.append(t)
    lst = V/'_list.txt'; lst.write_text(''.join(f"file '{t}'\n" for t in tmp))
    subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', '-movflags', '+faststart', str(out)], check=True)
    for t in tmp:
        t.unlink()
    lst.unlink()
full = [d for d in outs if d.name.startswith('full_')]; close = [d for d in outs if not d.name.startswith('full_')]
mp4(full, V/'HM55_vs_HM56_motion_full.mp4'); mp4(close, V/'HM55_vs_HM56_neck_knee_closeup.mp4')
subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(FR/'full_Run_JOIN/%04d.png'), '-vf', 'fps=15,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse', str(V/'HM55_vs_HM56_run.gif')], check=True)
lists.unlink()
for p in sorted(V.glob('*.mp4')) + sorted(V.glob('*.gif')):
    rec.setdefault('outputs', {})[p.name] = {'bytes': p.stat().st_size, 'sha256': hc.sha256(p)}
probe = subprocess.run([shutil.which('ffprobe'), '-v', 'error', '-show_entries', 'stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_frames', '-of', 'json', str(V/'HM55_vs_HM56_motion_full.mp4')], capture_output=True, text=True).stdout
rec['ffprobe_full'] = json.loads(probe); hc.write_json(hc.BUILD/'qa/anim_video56.json', rec); print('VIDEO OK', rec['outputs']); hc.finish()
