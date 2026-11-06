"""Classify card-triangle contacts in a hair (+face) GLB by obstacle and by position along the card (UV v:
root v=1 .. tip v=0). Root-band contacts (v >= 1-ROOT) lie where the card texture alpha is ~0 (root fade)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy  # noqa: F401  (provides mathutils)
from mathutils.bvhtree import BVHTree
import glb_io

ROOT = 0.22      # card texture root fade band (make_hair_textures.fc_root_fade)


def parts(path):
    g, b = glb_io.read_glb(path); out = {}
    for n in g['nodes']:
        if 'mesh' not in n:
            continue
        for p in g['meshes'][n['mesh']]['primitives']:
            V = glb_io.accessor(g, b, p['attributes']['POSITION']).astype(float); I = glb_io.accessor(g, b, p['indices']).ravel().reshape(-1, 3)
            uv = glb_io.accessor(g, b, p['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in p['attributes'] else None
            out[n['name'] + '/' + g['materials'][p['material']]['name']] = (V, I, uv)
    return out


def classify(path):
    P = parts(path); cards = [k for k in P if k.endswith('_Cards') or k.endswith('slot_13')]
    res = {}
    for ck in cards:
        V, I, uv = P[ck]
        tb = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(int(i) for i in t) for t in I], all_triangles=True, epsilon=0.0)
        vmax = 1 - uv[I][:, :, 1].min(1) if uv is not None else None      # glTF v is flipped: blender v = 1 - gltf v
        for ok, (OV, OI, _) in P.items():
            if ok == ck:
                continue
            to = BVHTree.FromPolygons([tuple(v) for v in OV], [tuple(int(i) for i in t) for t in OI], all_triangles=True, epsilon=0.0)
            pairs = sorted(set(tb.overlap(to)))
            if not pairs:
                continue
            ct = sorted({i for i, j in pairs})
            root = [i for i in ct if vmax is not None and vmax[i] >= 1 - ROOT]
            res[f'{ck} | {ok}'] = {'pairs': len(pairs), 'card_triangles': len(ct), 'card_triangles_in_root_fade': len(root),
                                   'card_triangles_beyond_root': len(ct) - len(root)}
    return res


if __name__ == '__main__':
    print(json.dumps({Path(a).name: classify(a) for a in sys.argv[1:]}, indent=1))
