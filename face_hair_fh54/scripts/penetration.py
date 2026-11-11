"""Dense radial penetration probe: how far skin pokes outside a hair cap (or cap below skin).
Samples every skin triangle with a barycentric grid (incl. edges). Returns worst depths."""
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def skin_samples(objs, n=6):
    pts = []
    for ob in objs:
        m = ob.data; mw = np.array(ob.matrix_world); co = np.array([v.co[:] for v in m.vertices])
        co = (mw[:3, :3] @ co.T).T + mw[:3, 3]
        bary = [(i/n, j/n, 1 - i/n - j/n) for i in range(n+1) for j in range(n+1-i)]
        B = np.array(bary)
        for p in m.polygons:
            vs = list(p.vertices)
            for k in range(1, len(vs)-1):
                tri = co[[vs[0], vs[k], vs[k+1]]]
                pts.append(B @ tri)
    return np.concatenate(pts)


def radial_depth(cap_verts, cap_tris, pts, centre):
    """For each skin point: (skin radius) - (cap radius) along the ray from centre. >0 = skin outside cap."""
    C = np.asarray(centre); bvh = BVHTree.FromPolygons([tuple(v) for v in cap_verts], cap_tris, epsilon=0.0)
    out = np.full(len(pts), np.nan); hit_tri = np.full(len(pts), -1)
    for i, p in enumerate(pts):
        d = p - C; r = np.linalg.norm(d); d = d/r
        loc, n, ti, dist = bvh.ray_cast(Vector(C + d*0.5), Vector(-d), 0.5)
        if loc is not None:
            out[i] = r - (np.array(loc) - C) @ d; hit_tri[i] = ti
    return out, hit_tri
