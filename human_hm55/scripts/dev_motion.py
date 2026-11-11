"""Development: motion sheet from an exported player GLB."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy, numpy as np
import hm_common as hc, hm_render as hr, hm_glbscene as gs
glb, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
arm, meshes = gs.load_player(glb); print('actions', gs.action_names())
SHOTS = [('Run', [0, 5, 10, 15]), ('Kick', [8, 14, 19, 25]), ('ThrowIn', [0, 13, 20, 29]), ('Header', [9, 17, 21, 30]), ('LookAround', [15, 45, 70, 80])]
sc, cam, T = hr.setup(res=(300, 480), samples=20, ortho=2.15, target=(0, 0, 0.95))
from PIL import Image
sheet = Image.new('RGB', (300*8, 480*len(SHOTS)))
for r, (act, frames) in enumerate(SHOTS):
    for c, f in enumerate(frames):
        gs.pose(arm, 'TM_HM55_' + act, f); hips = gs.bone_head(arm, 'Hips'); tgt = (float(hips[0]), float(hips[1]), 0.98)
        for k, v in enumerate(('quarter_L', 'side_L')):
            hr.aim(cam, tgt, v, 6); sc.render.filepath = str(out/f'{act}_{f:03d}_{v}.png'); bpy.ops.render.render(write_still=True); sheet.paste(Image.open(sc.render.filepath), ((c*2 + k)*300, r*480))
sheet.save(out/'motion_sheet.png'); hc.finish()
