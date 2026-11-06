"""Visual size of transparent draw-order flips: per sweep frame, area of head pixels where the bounds-sorted
render differs (>30/255 per channel sum/3) from the as-authored render at the same camera."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
d = Path(sys.argv[1]); orders = json.loads((d/'sweep_orders.json').read_text()); bg = np.array([0x3a, 0x41, 0x50], float); out = {}
for m in orders['models']:
    S = []; S8 = []
    for i in range(71):
        a = np.asarray(Image.open(d/f'{m}_authored_{i:03}.png').convert('RGB')).astype(float)
        b = np.asarray(Image.open(d/f'{m}_bounds_{i:03}.png').convert('RGB')).astype(float)
        head = (np.abs(a - bg).sum(2) > 12) | (np.abs(b - bg).sum(2) > 12)
        dd = np.abs(a - b).sum(2)/3; S.append(float(((dd > 30) & head).sum()/max(head.sum(), 1))); S8.append(float(((dd > 8) & head).sum()/max(head.sum(), 1)))
    S = np.array(S); S8 = np.array(S8); o = orders['models'][m]['bounds']
    flips = [i for i, (x, y) in enumerate(zip(o, o[1:])) if x != y]
    out[m] = {'transparent_primitives': o[0], 'order_flips_in_sweep': len(flips), 'flip_frames_elevation_deg': [-20 + 1.5*(i+1) for i in flips],
              "max_pct_head_pixels_changed_by_order": round(100*float(S.max()), 3), "max_pct_changed_over_8_of_255": round(100*float(S8.max()), 3), 'frames_with_any_order_change_over_0.5pct': int((S > 0.005).sum())}
    print(m, json.dumps(out[m]))
(d/'flip_analysis.json').write_text(json.dumps(out, indent=1))
