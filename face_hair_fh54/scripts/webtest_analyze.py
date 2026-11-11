"""Analyse the three.js orbit renders. Per frame: E = mean |render - reference| over the head region
(reference = same GLB with alpha-test + depth-write, i.e. correct occlusion, hard strand edges).
Sorting error = mean E (authored / bounds-sorted). Flicker = frame-to-frame jumps of E along the orbit."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
d = Path(sys.argv[1]); out = {}
models = ['FACE52', 'FH53_H1', 'FH54_H1', 'FH53_H2', 'FH54_H2', 'FH53_H3', 'FH54_H3', 'FH53_H4', 'FH54_H4']
bg = np.array([0x3a, 0x41, 0x50], float)
def load(p):
    return np.asarray(Image.open(p).convert('RGB')).astype(float)
for m in models:
    row = {}
    ref = [load(d/f'{m}_reference_{i:03}.png') for i in range(120)]
    for mode in ('authored', 'bounds'):
        E = []; big = []
        for i in range(120):
            a = load(d/f'{m}_{mode}_{i:03}.png'); r = ref[i]
            head = (np.abs(r - bg).sum(2) > 12) | (np.abs(a - bg).sum(2) > 12)
            diff = np.abs(a - r).sum(2)
            E.append(float(diff[head].mean())/3); big.append(float((diff[head] > 120).mean()))
        E = np.array(E); jumps = np.abs(np.diff(np.r_[E, E[:1]]))
        row[mode] = {'mean_error': round(float(E.mean()), 3), 'max_error': round(float(E.max()), 3),
                     'pixels_badly_wrong_pct_mean': round(100*float(np.mean(big)), 3),
                     'flicker_mean_jump': round(float(jumps.mean()), 3), 'flicker_max_jump': round(float(jumps.max()), 3),
                     'frames_with_jump_over_2': int((jumps > 2.0).sum())}
    out[m] = row
    print(m, json.dumps(row))
(d/'webtest_analysis.json').write_text(json.dumps(out, indent=1))
