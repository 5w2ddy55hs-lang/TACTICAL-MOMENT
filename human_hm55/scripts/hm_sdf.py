"""Small signed-distance toolkit (numpy). Shapes are smooth unions of ellipsoids and tapered capsules; a mesh
is obtained by casting rays from an inner axis and taking the outermost surface crossing, which gives a clean
ring/column quad grid. All shape numbers in HM55 are authored here in code - no mesh is imported or traced."""
import numpy as np


def rot_xyz(rx=0.0, ry=0.0, rz=0.0):
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def ellipsoid(p, c, r, R=None):
    q = p - np.asarray(c, float)
    if R is not None:
        q = q @ R          # world -> local (R columns are the local axes)
    r = np.asarray(r, float); k0 = np.linalg.norm(q/r, axis=-1); k1 = np.linalg.norm(q/(r*r), axis=-1)
    return np.where(k1 > 1e-12, k0*(k0 - 1.0)/np.maximum(k1, 1e-12), -r.min())


def round_cone(p, a, b, r1, r2):
    a = np.asarray(a, float); b = np.asarray(b, float); ba = b - a; l2 = ba @ ba; rr = r1 - r2; a2 = l2 - rr*rr; il2 = 1.0/l2
    pa = p - a; y = pa @ ba; z = y - l2; w = pa*l2 - ba*y[..., None]; x2 = (w*w).sum(-1); y2 = y*y*l2; z2 = z*z*l2
    k = np.sign(rr)*rr*rr*x2
    d = (np.sqrt(np.maximum(x2*a2*il2, 0)) + y*rr)*il2 - r1
    d = np.where(np.sign(y)*a2*y2 < k, np.sqrt(x2 + y2)*il2 - r1, d)
    d = np.where(np.sign(z)*a2*z2 > k, np.sqrt(x2 + z2)*il2 - r2, d)
    return d


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0)/k
    return np.minimum(a, b) - h*h*k*0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def union(parts, k):
    """parts: list of (distance array, k_override or None)"""
    d = None
    for x in parts:
        v, kk = x if isinstance(x, tuple) else (x, None)
        d = v if d is None else smin(d, v, k if kk is None else kk)
    return d


def outer_hit(f, origins, dirs, tmax, steps=96, iters=28):
    """Largest t in (0, tmax] with f(o + t d) = 0 (outermost surface along each ray). f takes (N,3) points."""
    O = np.asarray(origins, float); D = np.asarray(dirs, float); M = len(O)
    ts = np.linspace(tmax, 0.0, steps)
    vals = np.stack([f(O + D*t) for t in ts], 1)                    # (M, steps), from far to near
    inside = vals < 0
    first = np.argmax(inside, axis=1)                               # first inside sample when walking inwards
    ok = inside.any(axis=1) & (first > 0)
    hi = ts[np.maximum(first - 1, 0)]; lo = ts[first]               # f(hi) >= 0 (outside), f(lo) < 0 (inside)
    for _ in range(iters):
        mid = 0.5*(hi + lo); v = f(O + D*mid[:, None]); ins = v < 0
        lo = np.where(ins, mid, lo); hi = np.where(ins, hi, mid)
    t = 0.5*(hi + lo)
    return np.where(ok, t, np.nan)


def gradient(f, p, eps=1e-4):
    p = np.asarray(p, float); g = np.zeros_like(p)
    for i in range(3):
        e = np.zeros(3); e[i] = eps
        g[..., i] = f(p + e) - f(p - e)
    n = np.linalg.norm(g, axis=-1, keepdims=True)
    return g/np.maximum(n, 1e-12)
