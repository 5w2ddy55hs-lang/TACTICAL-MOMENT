"""Development: rigged clay figure in test poses (rest, kick, look-around, arms up)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_assemble as ha, hm_render as hr
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
hc.reset_scene(); body, binfo = ha.build_body(); head, hinfo = ha.build_head(); arm = ha.build_rig(); ha.bind(body, arm); ha.bind(head, arm)
print('body verts', len(body.data.vertices), 'welded', binfo['_welded_vertices'], 'head verts', len(head.data.vertices), 'bones', len(arm.data.bones))
POSES = {'rest': {},
         'kick': {'UpperLeg_R': (-55, 0, 0), 'LowerLeg_R': (25, 0, 0), 'UpperLeg_L': (12, 0, 0), 'LowerLeg_L': (10, 0, 0), 'Spine': (8, 0, -8), 'UpperArm_L': (-30, 20, 0), 'UpperArm_R': (35, -20, 0), 'Head': (10, 0, 0)},
         'look': {'Neck': (0, 0, 28), 'Head': (-8, 0, 38), 'UpperArm_L': (0, 14, 0), 'UpperArm_R': (0, -14, 0)},
         'throw': {'UpperArm_L': (-150, 10, 0), 'UpperArm_R': (-150, -10, 0), 'LowerArm_L': (-40, 0, 0), 'LowerArm_R': (-40, 0, 0), 'Spine': (12, 0, 0), 'Chest': (10, 0, 0), 'Neck': (8, 0, 0), 'Head': (12, 0, 0)},
         'nod': {'Neck': (22, 0, 0), 'Head': (25, 0, 0)}}
sc, cam, T = hr.setup(res=(360, 640), samples=16, ortho=2.0, target=(0, 0, 0.95), clay=True)
from PIL import Image
views = ['front', 'quarter_L', 'side_L']; sheet = Image.new('RGB', (360*len(views)*len(POSES), 640)); k = 0
for name, pose in POSES.items():
    ha.set_pose(arm, pose)
    for v in views:
        hr.aim(cam, T, v, 6); sc.render.filepath = str(out/f'pose_{name}_{v}.png'); bpy.ops.render.render(write_still=True); sheet.paste(Image.open(sc.render.filepath), (k*360, 0)); k += 1
sheet.save(out/'pose_sheet.png')
hc.save_blend(out/'dev_rig.blend'); hc.finish()
