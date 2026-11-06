"""Render the provisional rigid vs weighted neck binding at selected frames of the existing clips (review files)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import fh53_common as fc, review_ref04 as rv
res = json.loads((fc.BUILD/'qa/anim_ref04.json').read_text())
out = fc.BUILD/'renders/anim'; out.mkdir(parents=True, exist_ok=True); rows = []
SH = [('neck_side', (3, 0, 1.55), (0, 0, 1.53), .30, 384, 384), ('neck_back', (0, 3, 1.55), (0, 0, 1.53), .30, 384, 384),
      ('neck_front', (0, -3, 1.55), (0, 0, 1.53), .30, 384, 384), ('body_quarter', (4.2, -4.2, 1.1), (0, 0, .93), 2.05, 384, 768)]
for mode in ('RIGID', 'WEIGHTED'):
    for act_name in ('REF_gamemtn0_id0039_normalized_phase', 'REF_gamemtn0_id1012_normalized_phase'):
        info = res['runs'][f'F1_H1_{mode.lower()}']['actions'][act_name]
        for tag, frame in (('start', 1), ('worst', info['gap_max_frame'])):
            bpy.ops.wm.open_mainfile(filepath=str(fc.BUILD/'models/review'/f'TM_FH54_REVIEW_REF04_ANIM_{mode}_F1_H1.blend'))
            rig = bpy.data.objects['REF_SourceRig21']; rig.animation_data.action = bpy.data.actions[act_name]
            for t in rig.animation_data.nla_tracks:
                t.mute = True
            sc, cam = rv.setup_scene(384, 384, 16); sc.frame_set(frame)
            short = act_name.split('_')[2]
            for name, loc, aim, scale, sx, sy in SH:
                p = rv.shoot(sc, cam, loc, aim, scale, out/f'{mode}_{short}_{tag}_f{frame:02}_{name}.png', sx, sy)
                rows.append({'png': p.name, 'mode': mode, 'action': act_name, 'frame': frame, 'sha256': fc.sha256(p)})
fc.write_json(fc.BUILD/'qa/anim_render_ledger.json', rows); print('ANIMRENDERS', len(rows))
fc.finish()
