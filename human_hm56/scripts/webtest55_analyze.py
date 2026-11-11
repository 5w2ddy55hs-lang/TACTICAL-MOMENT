"""Analyse the HM55 browser captures: transparent draw-order sensitivity (cards first vs last) and the effect of
back-face culling on the body (inside-out faces would disappear). Writes $HM_BUILD/qa/webtest55_analysis.json and
a contact sheet of the browser frames."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image
import hm_common as hc
W = hc.BUILD/'webtest/out'; bg = np.array([0x3a, 0x41, 0x50], float); res = {}
models = sorted({p.name.split('_rest_')[0] for p in W.glob('*_rest_front.png')})
def diff_pct(a, b, thr=8):
    A = np.asarray(Image.open(a).convert('RGB'), float); B = np.asarray(Image.open(b).convert('RGB'), float)
    fg = (np.abs(A - bg).sum(2) > 12) | (np.abs(B - bg).sum(2) > 12); d = np.abs(A - B).sum(2)/3
    return round(100*float(((d > thr) & fg).sum()/max(fg.sum(), 1)), 3)
for m in models:
    res[m] = {'order_changed_pixels_pct': {lab: diff_pct(W/f'{m}_order_{lab}_cardsLast.png', W/f'{m}_order_{lab}_cardsFirst.png') for lab in ('q', 'top', 'back', 'side')},
              'front_only_vs_double_sided_changed_pixels_pct': diff_pct(W/f'{m}_side_frontOnly.png', W/f'{m}_side_double.png')}
hc.write_json(hc.BUILD/'qa/webtest55_analysis.json', res)
m = models[0]; names = [f'{m}_rest_front', f'{m}_rest_side', f'{m}_rest_back', f'{m}_Run_0167_q', f'{m}_Kick_0633_q', f'{m}_Kick_0833_side', f'{m}_LookAround_0500_q', f'{m}_ThrowIn_0433_side']
ims = [Image.open(W/(n + '.png')).convert('RGB') for n in names if (W/(n + '.png')).exists()]
if ims:
    w, h = ims[0].size; sheet = Image.new('RGB', (w*4, h*2))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 4)*w, (i//4)*h))
    (hc.BUILD/'images').mkdir(exist_ok=True); sheet.resize((1080, int(1080*h*2/(w*4))), Image.LANCZOS).save(hc.BUILD/'images/M10_browser_threejs.jpg', quality=90)
print(json.dumps(res))
