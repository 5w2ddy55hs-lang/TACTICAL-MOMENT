"""Pairwise difference between face renders (same hair H0, same camera) at small display sizes, FH53 vs FH54.
A simple, objective proxy for 'the faces look like different people at game size' - not a perception test."""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image
import fh53_common as fc
d = fc.BUILD/'renders/SMALL'; bg = np.array([0.22, 0.27, 0.34])*255*0 + np.array([96, 108, 125])   # approx review background
out = {}
for gen in ('FH53', 'FH54'):
    tags = ['FACE52'] + [f'{gen}_F{i}_H0' for i in (1, 2, 3)]
    for px in (64, 128):
        for view in ('front', 'quarter_R'):
            ims = {t: np.asarray(Image.open(d/f'{t}_{px}px_{view}.png').convert('RGB')).astype(float) for t in tags}
            vals = []
            for a, b in itertools.combinations(tags, 2):
                A, Bm = ims[a], ims[b]
                fg = (np.abs(A - A[0, 0]).sum(2) > 18) | (np.abs(Bm - Bm[0, 0]).sum(2) > 18)
                vals.append(float(np.abs(A - Bm).sum(2)[fg].mean()/3))
            out[f'{gen}_{px}px_{view}'] = {'pairs': len(vals), 'mean_pair_diff': round(float(np.mean(vals)), 2), 'min_pair_diff': round(float(np.min(vals)), 2)}
fc.write_json(fc.BUILD/'qa/face_distinct54.json', out)
for k, v in out.items():
    print(k, v)
