"""HM56 body (from HM55; athletic torso, natural shoulders, knee / calf / ankle / boot shapes): original shapes (smooth unions of ellipsoids / tapered capsules) sampled as ring x column tubes.
Parts: shirt torso (open hem, collar ring), short sleeves (ball-jointed at the shoulder), arms, mitten hands,
shorts (pelvis welded to two legs through a crotch vertex), legs with socks, boots. World frame: Z up, ground
z = 0, faces -Y, +X = character's left. All dimensions are authored below from generic adult proportions."""
import math
import numpy as np
import hm_sdf as S
from hm_common import smoothstep

# ---------------------------------------------------------------- skeleton (rest pose joint positions, world metres)
HEIGHT = 1.78
HEAD_PIVOT = np.array([0.0, 0.012, 1.615])            # head-local origin of hm_head in world space
ARM_DIR = np.array([math.sin(math.radians(24)), 0.0, -math.cos(math.radians(24))])
FORE_DIR = np.array([0.385, -0.130, -0.914]); FORE_DIR /= np.linalg.norm(FORE_DIR)
J = {'Hips': np.array([0.0, 0.010, 0.960]), 'Spine': np.array([0.0, 0.012, 1.080]), 'Chest': np.array([0.0, 0.018, 1.240]),
     'Neck': np.array([0.0, 0.030, 1.475]), 'Head': HEAD_PIVOT, 'HeadEnd': np.array([0.0, 0.012, 1.780]),
     'Shoulder': np.array([0.030, 0.022, 1.440]), 'UpperArm': np.array([0.186, 0.020, 1.412]),
     'UpperLeg': np.array([0.092, 0.010, 0.925]), 'LowerLeg': np.array([0.098, -0.002, 0.505]), 'Foot': np.array([0.102, 0.018, 0.085]),
     'Toes': np.array([0.106, -0.112, 0.024]), 'ToesEnd': np.array([0.108, -0.188, 0.024])}
J['LowerArm'] = J['UpperArm'] + ARM_DIR*0.295
J['Hand'] = J['LowerArm'] + FORE_DIR*0.255
J['HandEnd'] = J['Hand'] + FORE_DIR*0.185
SLEEVE_LEN = 0.165
SOCK_TOP_Z = 0.452
SHORTS_HEM_Z = 0.630
SHIRT_HEM_Z = 0.875
COLLAR = dict(c=(0.0, 0.0430, 1.4980), rx=0.0725, ry=0.0745, front_drop=0.030)     # collar ring around the neck


import hm_head as _hh_mod
_NECK = _hh_mod.neck_sdf()


def mx(p):
    return np.array([-p[0], p[1], p[2]])


# ---------------------------------------------------------------- shapes
def _limb_frame(d_):
    """Local axes for an ellipsoid aligned with a limb: (sideways, front-back, along the limb)."""
    y_ = np.cross(d_, [1.0, 0, 0]); y_ /= np.linalg.norm(y_); return np.stack([np.cross(y_, d_), y_, d_], 1)


def deltoid(sgn, extra=0.0):
    a = J['UpperArm']*np.array([sgn, 1, 1]); dr = ARM_DIR*np.array([sgn, 1, 1])
    return lambda p: S.ellipsoid(p, a + dr*0.040 + np.array([0.0, 0.002, 0.0]), (0.037 + extra, 0.047 + extra, 0.060 + extra), _limb_frame(dr))


def torso_sdf(p):
    """Shirt surface (about 8-12 mm over the body): hem, tapered waist, rib cage, chest, back, trapezius slope, deltoids."""
    d = S.ellipsoid(p, (0, 0.012, 0.905), (0.180, 0.127, 0.200))                       # hem over the hips (slightly loose)
    d = S.smin(d, S.ellipsoid(p, (0, 0.014, 1.060), (0.150, 0.106, 0.130)), 0.07)      # waist
    d = S.smin(d, S.ellipsoid(p, (0, 0.006, 1.235), (0.170, 0.116, 0.165)), 0.07)      # rib cage
    d = S.smin(d, S.ellipsoid(p, (0, 0.024, 1.385), (0.168, 0.094, 0.062)), 0.05)      # upper chest / shoulder girdle
    d = S.smin(d, S.smax(_NECK(np.asarray(p, float) - HEAD_PIVOT) - 0.0095, p[..., 2] - (COLLAR['c'][2] - 0.004), 0.010), 0.028)   # yoke wraps the neck base (9.5 mm over the skin), up to the collar
    for sgn in (1, -1):
        d = S.smin(d, S.ellipsoid(p, (sgn*0.074, -0.068, 1.305), (0.072, 0.042, 0.058)), 0.045)     # pectoral
        d = S.smin(d, S.ellipsoid(p, (sgn*0.088, 0.066, 1.265), (0.072, 0.052, 0.125)), 0.055)      # latissimus / back
        d = S.smin(d, S.round_cone(p, (sgn*0.055, 0.036, 1.494), (sgn*0.180, 0.020, 1.430), 0.030, 0.034), 0.050)   # trapezius slope to the acromion
        d = S.smin(d, deltoid(sgn, 0.008)(p), 0.030)                                   # deltoid (+ cloth) instead of a ball
    return d


def sleeve_sdf(sgn):
    a = J['UpperArm']*np.array([sgn, 1, 1]); dr = ARM_DIR*np.array([sgn, 1, 1]); dl = deltoid(sgn, 0.009)
    def f(p):
        d = S.round_cone(p, a + dr*0.045, a + dr*SLEEVE_LEN, 0.064, 0.060)            # rounded end sits inside the shoulder
        return S.smin(d, dl(p), 0.02)
    return f


def arm_sdf(sgn):
    m = np.array([sgn, 1, 1]); a = J['UpperArm']*m; e = J['LowerArm']*m; w = J['Hand']*m; da = ARM_DIR*m; df = FORE_DIR*m
    def frame(d_):                                                    # local axes: (sideways, front-back, along the limb)
        y_ = np.cross(d_, [1.0, 0, 0]); y_ /= np.linalg.norm(y_); return np.stack([np.cross(y_, d_), y_, d_], 1)
    Ra, Rf = frame(da), frame(df)
    def f(p):
        d = S.round_cone(p, a, e, 0.053, 0.042)
        d = S.smin(d, S.ellipsoid(p, a + da*0.135 + np.array([0, -0.006, 0]), (0.050, 0.056, 0.090), Ra), 0.02)  # biceps / triceps mass, along the arm
        d = S.smin(d, S.round_cone(p, e, w, 0.042, 0.030), 0.012)
        d = S.smin(d, S.ellipsoid(p, e + df*0.080, (0.045, 0.049, 0.075), Rf), 0.02)                          # forearm belly
        return d
    return f


def hand_sdf(sgn):
    m = np.array([sgn, 1, 1]); w = J['Hand']*m; df = FORE_DIR*m
    side = np.cross(df, np.array([sgn, 0, 0.35])); side /= np.linalg.norm(side)        # across the palm (front-back)
    nrm = np.cross(side, df)                                                           # palm normal (toward the thigh)
    R = np.stack([nrm, side, df], 1)
    def f(p):
        d = S.ellipsoid(p, w + df*0.085, (0.0165, 0.0440, 0.0920), R)                  # palm + fingers (mitten)
        d = S.smin(d, S.ellipsoid(p, w + df*0.150, (0.0130, 0.0370, 0.0420), R), 0.015)
        d = S.smin(d, S.round_cone(p, w + df*0.035 - side*0.024, w + df*0.108 - side*0.054 - nrm*0.004, 0.0135, 0.0105), 0.010)   # thumb (front side)
        d = S.smin(d, S.round_cone(p, w - df*0.03, w + df*0.03, 0.030, 0.028), 0.012)  # wrist
        return d
    return f, R


def shorts_sdf(p):
    d = S.ellipsoid(p, (0, 0.012, 0.955), (0.165, 0.115, 0.105))
    for sgn in (1, -1):
        m = np.array([sgn, 1, 1]); d = S.smin(d, S.round_cone(p, J['UpperLeg']*m, np.array([0.106*sgn, 0.004, 0.580]), 0.080, 0.108), 0.03)
    return d


def shorts_leg_sdf(sgn):
    """One shorts leg only (the ring rays must not run into the other leg); flat inner face near the mid-plane."""
    m = np.array([sgn, 1, 1])
    def f(p):
        d = S.round_cone(p, J['UpperLeg']*m, np.array([0.106*sgn, 0.004, 0.580]), 0.080, 0.108)
        d = S.smin(d, S.ellipsoid(p, (0, 0.012, 0.955), (0.165, 0.115, 0.105)), 0.03)
        return S.smax(d, 0.007 - sgn*p[..., 0], 0.010)
    return f


def leg_sdf(sgn):
    m = np.array([sgn, 1, 1]); h = J['UpperLeg']*m; k = J['LowerLeg']*m; a = J['Foot']*m; inner = -sgn
    def f(p):
        d = S.round_cone(p, h, k, 0.084, 0.050)
        d = S.smin(d, S.ellipsoid(p, h + (k - h)*0.48 + np.array([0, -0.016, 0]), (0.074, 0.078, 0.160)), 0.03)        # quadriceps
        d = S.smin(d, S.ellipsoid(p, k + np.array([inner*0.030, -0.018, 0.090]), (0.036, 0.036, 0.062)), 0.020)         # vastus medialis (teardrop above the inner knee)
        d = S.smin(d, S.ellipsoid(p, h + (k - h)*0.52 + np.array([0, 0.028, 0]), (0.066, 0.062, 0.140)), 0.03)         # hamstring
        d = S.smin(d, S.ellipsoid(p, k + np.array([0, -0.034, 0.006]), (0.029, 0.020, 0.033)), 0.010)                  # patella
        for sx in (1, -1):
            d = S.smin(d, S.ellipsoid(p, k + np.array([sx*0.034, -0.004, -0.004]), (0.020, 0.034, 0.030)), 0.012)       # femoral condyles
        d = S.smin(d, S.round_cone(p, k, a, 0.050, 0.033), 0.012)                                                     # shin bone, slim ankle
        d = S.smin(d, S.ellipsoid(p, k + (a - k)*0.27 + np.array([inner*0.015, 0.034, 0]), (0.034, 0.038, 0.088)), 0.02)  # calf, inner head
        d = S.smin(d, S.ellipsoid(p, k + (a - k)*0.24 + np.array([-inner*0.016, 0.030, 0]), (0.030, 0.034, 0.080)), 0.02) # calf, outer head
        d = S.smin(d, S.round_cone(p, k + (a - k)*0.55 + np.array([0, 0.030, 0]), a + np.array([0, 0.034, 0.020]), 0.020, 0.012), 0.012)   # Achilles tendon
        d = S.smin(d, S.ellipsoid(p, k + (a - k)*0.42 + np.array([0, -0.026, 0]), (0.034, 0.028, 0.150)), 0.02)        # shin guard under the sock
        return d
    return f


def boot_sdf(sgn):
    m = np.array([sgn, 1, 1]); a = J['Foot']*m; t = J['Toes']*m; te = J['ToesEnd']*m
    def f(p):
        d = S.round_cone(p, a + np.array([0, 0.002, 0.040]), a + np.array([0, 0.006, -0.032]), 0.046, 0.046)          # ankle collar
        d = S.smin(d, S.ellipsoid(p, a + np.array([0.0, 0.032, -0.050]), (0.036, 0.046, 0.036)), 0.018)              # heel counter
        d = S.smin(d, S.round_cone(p, a + np.array([0, -0.010, -0.048]), t + np.array([0, 0, 0.004]), 0.037, 0.026), 0.020)   # instep
        d = S.smin(d, S.ellipsoid(p, (t + te)/2 + np.array([0.003*sgn, 0.014, 0.000]), (0.041, 0.060, 0.021)), 0.018)  # low toe box
        c = (a + te)/2; d = S.smin(d, S.ellipsoid(p, np.array([c[0], c[1] - 0.004, 0.011]), (0.045, 0.150, 0.011)), 0.006)   # sole plate
        return S.smax(d, 0.003 - p[..., 2], 0.004)                                                                  # sole on the ground
    return f


# ---------------------------------------------------------------- tube sampler
class Axis:
    """Rounded polyline: position and tangent as functions of arc length."""
    def __init__(self, pts, round_len=0.05):
        self.P = np.array(pts, float); seg = np.linalg.norm(np.diff(self.P, axis=0), axis=1); self.cum = np.concatenate([[0], np.cumsum(seg)]); self.L = self.cum[-1]; self.w = round_len
    def raw(self, t):
        t = float(np.clip(t, -1.0, self.L + 1.0)); i = int(np.clip(np.searchsorted(self.cum, t) - 1, 0, len(self.P) - 2)); d = self.P[i + 1] - self.P[i]; u = (t - self.cum[i])/np.linalg.norm(d)
        return self.P[i] + d*u
    def pos(self, t):
        return (self.raw(t - self.w/2) + 2*self.raw(t) + self.raw(t + self.w/2))/4 if self.w > 0 else self.raw(t)
    def tan(self, t):
        d = self.raw(t + self.w/2) - self.raw(t - self.w/2) if self.w > 0 else self.raw(t + 1e-4) - self.raw(t - 1e-4)
        return d/np.linalg.norm(d)


def tube(sdf, axis, ts, angles_deg, ref, tmax=0.35, angle_fn=None):
    """Rings perpendicular to the axis at arc lengths ts. Angle 0 points along `ref` projected into the first ring
    plane and is then parallel-transported along the axis; angles increase toward tangent x e0.
    angle_fn(i) may return per-ring angles (degrees). Returns V (R, C, 3)."""
    R = len(ts); e0 = None; rows = []
    for i, t in enumerate(ts):
        a = np.radians(np.asarray(angle_fn(i) if angle_fn else angles_deg, float)); C = len(a)
        o = axis.pos(t); T = axis.tan(t); base = np.asarray(ref, float) if e0 is None else e0
        e0 = base - (base @ T)*T; e0 /= np.linalg.norm(e0); e1 = np.cross(T, e0)
        D = np.cos(a)[:, None]*e0 + np.sin(a)[:, None]*e1
        h = S.outer_hit(sdf, np.repeat(o[None], C, 0), D, tmax)
        if np.isnan(h).any():
            raise ValueError('tube ray missed at t=%.3f' % t)
        rows.append(o + D*h[:, None])
    return np.array(rows)


class Part:
    """One UV chart: ring x column grid closed around, optional poles at either end."""
    def __init__(self, name, material, rect, V, pole_end=None, pole_start=None, group=None):
        self.name, self.material, self.rect, self.V, self.pole_end, self.pole_start = name, material, rect, np.asarray(V, float), pole_end, pole_start
        self.group = group or name
        i = self.V.shape[0]//2 - 1 if self.V.shape[0] > 3 else 0      # a ring pair in the middle: hem folds at the ends face the other way
        a, b, d = self.V[i, 0], self.V[i, 1], self.V[i + 1, 0]; c = self.V[i].mean(0)
        self.flip = bool(np.cross(b - a, d - a) @ (a - c) < 0)

    def mesh(self, base):
        V = self.V; R, C = V.shape[:2]; verts = [tuple(v) for v in V.reshape(-1, 3)]; vid = lambda i, j: base + i*C + (j % C)
        u0, v0, u1, v1 = self.rect
        seg = np.linalg.norm(np.diff(V, axis=0), axis=2).mean(1); cum = np.concatenate([[0], np.cumsum(seg)])
        e0 = np.linalg.norm(self.pole_start - V[0].mean(0)) if self.pole_start is not None else 0.0
        e1 = np.linalg.norm(self.pole_end - V[-1].mean(0)) if self.pole_end is not None else 0.0
        vv = v0 + (v1 - v0)*(e0 + cum)/(e0 + cum[-1] + e1); uu = lambda j: u0 + (u1 - u0)*j/C
        faces = []; uvs = []
        def add(f, uv):
            if self.flip:
                f, uv = f[::-1], uv[::-1]
            faces.append(tuple(f)); uvs.extend(uv)
        for i in range(R - 1):
            for j in range(C):
                add([vid(i, j), vid(i, j + 1), vid(i + 1, j + 1), vid(i + 1, j)], [(uu(j), vv[i]), (uu(j + 1), vv[i]), (uu(j + 1), vv[i + 1]), (uu(j), vv[i + 1])])
        if self.pole_end is not None:
            pid = base + len(verts); verts.append(tuple(self.pole_end))
            for j in range(C):
                add([vid(R - 1, j), vid(R - 1, j + 1), pid], [(uu(j), vv[R - 1]), (uu(j + 1), vv[R - 1]), (uu(j + 0.5), v1)])
        if self.pole_start is not None:
            pid = base + len(verts); verts.append(tuple(self.pole_start))
            for j in range(C):
                add([vid(0, j + 1), vid(0, j), pid], [(uu(j + 1), vv[0]), (uu(j), vv[0]), (uu(j + 0.5), v0)])
        return verts, faces, uvs


def fold_ring(ring, centre, shrink, shift):
    """Hem fold: the ring pulled toward the centre by `shrink` (fraction) and moved by `shift`."""
    ring = np.asarray(ring, float); c = np.asarray(centre, float)
    return c + (ring - c)*(1 - shrink) + np.asarray(shift, float)


# ---------------------------------------------------------------- atlas rectangles (u0, v0, u1, v1)
KIT_RECT = {'torso': (0.005, 0.455, 0.615, 0.995), 'sleeve_L': (0.635, 0.790, 0.810, 0.995), 'sleeve_R': (0.825, 0.790, 0.995, 0.995),
            'shorts': (0.005, 0.225, 0.615, 0.440), 'shorts_leg_L': (0.635, 0.560, 0.810, 0.775), 'shorts_leg_R': (0.825, 0.560, 0.995, 0.775),
            'sock_L': (0.635, 0.225, 0.810, 0.545), 'sock_R': (0.825, 0.225, 0.995, 0.545), 'boot_L': (0.005, 0.005, 0.300, 0.210), 'boot_R': (0.315, 0.005, 0.610, 0.210)}
SKIN_RECT = {'arm_L': (0.01, 0.01, 0.24, 0.99), 'arm_R': (0.26, 0.01, 0.49, 0.99), 'leg_L': (0.51, 0.30, 0.74, 0.99), 'leg_R': (0.76, 0.30, 0.99, 0.99)}
TORSO_Z = [SHIRT_HEM_Z, 0.900, 0.960, 1.030, 1.100, 1.170, 1.240, 1.310, 1.365]
TORSO_PHI = [12, 24, 35, 45, 54]
TORSO_O = np.array([0.0, 0.016, 1.365])
ANG16 = [k*22.5 for k in range(16)]
ANG8 = [k*45.0 for k in range(8)]
ANG10 = [k*36.0 for k in range(10)]


COLLAR_CLEAR = 0.0090          # HM56: the collar follows the neck cross-section at this distance


def collar_ring(angles_deg, clear=COLLAR_CLEAR, dz=0.0):
    """HM56: the collar opening is measured from the (shared, unscaled) neck of hm_head at the collar height, plus a
    constant clearance, instead of a fixed ellipse - so the shirt fits the neck and its trapezius flare evenly."""
    import hm_head as _hh
    c = COLLAR; a = np.radians(np.asarray(angles_deg, float)); z = c['c'][2] + dz - c['front_drop']*np.clip(np.cos(a), 0, 1)**2
    f = _hh.head_sdf(_hh.P0); O = np.stack([np.full_like(a, c['c'][0]), np.full_like(a, c['c'][1] - 0.012), z], 1) - HEAD_PIVOT
    D = np.stack([np.sin(a), -np.cos(a), np.zeros_like(a)], 1); t = S.outer_hit(f, O, D, 0.20)
    for _ in range(200):                                       # walk outward until the TRUE surface distance reaches the clearance
        short = f(O + D*t[:, None]) < clear
        if not short.any():
            break
        t = t + 0.0005*short
    return O + HEAD_PIVOT + D*t[:, None]


def build_parts():
    parts = []
    # ---- shirt torso
    rows = []
    for z in TORSO_Z:
        o = np.array([0.0, 0.012, z]); a = np.radians(ANG16); D = np.stack([np.sin(a), -np.cos(a), np.zeros_like(a)], 1)
        rows.append(o + D*S.outer_hit(torso_sdf, np.repeat(o[None], 16, 0), D, 0.4)[:, None])
    for phi in TORSO_PHI:
        a = np.radians(ANG16); ph = math.radians(phi); D = np.stack([math.cos(ph)*np.sin(a), -math.cos(ph)*np.cos(a), np.full_like(a, math.sin(ph))], 1)
        rows.append(TORSO_O + D*S.outer_hit(torso_sdf, np.repeat(TORSO_O[None], 16, 0), D, 0.4)[:, None])
    col = collar_ring(ANG16); cc_ = np.array(COLLAR['c'])
    rows.append(col); rows.append(collar_ring(ANG16, COLLAR_CLEAR - 0.0010, dz=-0.006))          # collar band turned inward, same clearance
    hem = rows[0]; rows.insert(0, fold_ring(hem, (0, 0.012, SHIRT_HEM_Z), 0.015, (0, 0, 0.012)))
    parts.append(Part('torso', 'kit', KIT_RECT['torso'], rows))
    for sgn, tag in ((1, 'L'), (-1, 'R')):
        m = np.array([sgn, 1, 1])
        # ---- sleeve (ball at the shoulder joint, open hem with a fold)
        a0 = J['UpperArm']*m; dr = ARM_DIR*m; ax = Axis([a0 - dr*0.08, a0 + dr*(SLEEVE_LEN + 0.02)], 0)
        V = tube(sleeve_sdf(sgn), ax, [0.068, 0.082, 0.100, 0.124, 0.156, 0.196, 0.08 + SLEEVE_LEN], ANG10, (0, -1, 0), 0.2)
        af_ = arm_sdf(sgn); V = np.concatenate([V, tube(lambda p, af_=af_: af_(p) - 0.0040, ax, [0.08 + SLEEVE_LEN - 0.012], ANG10, (0, -1, 0), 0.2)])
        o_ = a0 - dr*0.008; cap = o_ - dr*S.outer_hit(sleeve_sdf(sgn), o_[None], -dr[None], 0.2)[0]
        parts.append(Part('sleeve_' + tag, 'kit', KIT_RECT['sleeve_' + tag], V, pole_start=cap))
        # ---- arm + hand (one tube; starts hidden inside the sleeve)
        hs, _ = hand_sdf(sgn); af = arm_sdf(sgn); f = lambda p, af=af, hs=hs: S.smin(af(p), hs(p), 0.010)
        ax = Axis([a0, J['LowerArm']*m, J['Hand']*m, J['HandEnd']*m], 0.05)
        ts = [0.105, 0.170, 0.235, 0.270, 0.295, 0.322, 0.370, 0.430, 0.490, 0.530, 0.552, 0.580, 0.620, 0.660, 0.700, 0.724]
        V = tube(f, ax, ts, ANG8, (0, -1, 0), 0.16)
        tip = J['HandEnd']*m; parts.append(Part('arm_' + tag, 'skin', SKIN_RECT['arm_' + tag], V, pole_end=tip - FORE_DIR*m*0.004)); parts[-1].ring_t = ts + [ts[-1] + 0.02]
        # ---- thigh / knee (skin), ends hidden under the sock top
        lf = leg_sdf(sgn); ax = Axis([J['UpperLeg']*m, J['LowerLeg']*m, J['Foot']*m], 0.06)
        L1 = np.linalg.norm(J['LowerLeg'] - J['UpperLeg']); zt = lambda z: L1 + (J['LowerLeg'][2] - z)*np.linalg.norm(J['Foot'] - J['LowerLeg'])/(J['LowerLeg'][2] - J['Foot'][2]) if z < J['LowerLeg'][2] else (J['UpperLeg'][2] - z)*L1/(J['UpperLeg'][2] - J['LowerLeg'][2])
        # the part hidden inside the shorts is slimmer than the real thigh so it can never show through the cloth
        zs_leg = (0.700, 0.670, 0.640, 0.605, 0.570, 0.540, 0.505, 0.472, SOCK_TOP_Z - 0.012)
        V = np.concatenate([tube(lambda p, lf=lf, z=z: lf(p) + 0.022*float(smoothstep(SHORTS_HEM_Z + 0.004, SHORTS_HEM_Z + 0.045, z)), ax, [zt(z)], ANG10, (0, -1, 0), 0.2) for z in zs_leg])
        parts.append(Part('leg_' + tag, 'skin', SKIN_RECT['leg_' + tag], V))
        # ---- sock (leg surface + 3.5 mm) with a folded top, runs into the boot
        sf = lambda p, lf=lf: lf(p) - 0.0035
        V = tube(sf, ax, [zt(z) for z in (SOCK_TOP_Z, 0.405, 0.345, 0.280, 0.215, 0.160, 0.118)], ANG10, (0, -1, 0), 0.2)
        V = np.concatenate([tube(lambda p, lf=lf: lf(p) - 0.0012, ax, [zt(SOCK_TOP_Z - 0.008)], ANG10, (0, -1, 0), 0.2), V])
        parts.append(Part('sock_' + tag, 'kit', KIT_RECT['sock_' + tag], V))
        # ---- boot (tube bent from the ankle into the foot, toe pole)
        an = J['Foot']*m; bax = Axis([an + np.array([0, 0, 0.060]), an + np.array([0, 0.004, -0.043]), J['Toes']*m + np.array([0, 0, 0.006]), J['ToesEnd']*m + np.array([0, -0.012, 0.004])], 0.12)
        V = tube(boot_sdf(sgn), bax, [0.006, 0.035, 0.062, 0.088, 0.114, 0.142, 0.175, 0.210, 0.248, 0.285], ANG10, (0, -1, 0), 0.30)
        ztop = float(V[0][:, 2].mean()); V = np.concatenate([tube(lambda p, sf=sf: sf(p) - 0.0030, ax, [zt(ztop - 0.010)], ANG10, (0, -1, 0), 0.2), V])
        tip = S.outer_hit(boot_sdf(sgn), bax.pos(0.285)[None], bax.tan(0.285)[None], 0.12)[0]
        parts.append(Part('boot_' + tag, 'kit', KIT_RECT['boot_' + tag], V, pole_end=bax.pos(0.285) + bax.tan(0.285)*tip))
    # ---- shorts: pelvis rings, then each leg ring starts from half of the pelvis bottom ring + the crotch vertex
    rows = []
    for z in (0.985, 0.935, 0.890, 0.855):
        o = np.array([0.0, 0.012, z]); a = np.radians(ANG16); D = np.stack([np.sin(a), -np.cos(a), np.zeros_like(a)], 1)
        rows.append(o + D*S.outer_hit(shorts_sdf, np.repeat(o[None], 16, 0), D, 0.4)[:, None])
    parts.append(Part('shorts', 'kit', KIT_RECT['shorts'], rows)); P = rows[-1]
    M = np.array([0.0, 0.014, 0.828])
    L0 = np.concatenate([P[0:9], M[None]])                                   # front centre -> left side -> back centre -> crotch
    ax = Axis([J['UpperLeg'] + np.array([0.004, 0, 0.02]), np.array([0.106, 0.004, 0.560])], 0)
    def ring_angles(pts, t):
        o = ax.pos(t); T = ax.tan(t); e0 = np.array([0, -1.0, 0]) - (np.array([0, -1.0, 0]) @ T)*T; e0 /= np.linalg.norm(e0); e1 = np.cross(T, e0)
        return np.degrees(np.arctan2((pts - o) @ e1, (pts - o) @ e0))
    a0 = np.unwrap(np.radians(ring_angles(L0, 0.075)), period=2*np.pi); a0 = np.degrees(a0)
    uni = a0[0] + (a0[-1] - a0[0])/9.0*np.arange(10) if abs(a0[-1] - a0[0]) > 200 else a0
    span = -324.0 if a0[4] < a0[0] else 324.0; uni = a0[0] + span/9.0*np.arange(10)
    zs = [0.790, 0.710, SHORTS_HEM_Z]; tz = lambda z: (ax.P[0][2] - z)/(ax.P[0][2] - ax.P[1][2])*ax.L
    Vl = [L0]
    for i, z in enumerate(zs):
        w = (i + 1)/len(zs); ang = a0*(1 - w) + uni*w
        Vl.append(tube(shorts_leg_sdf(1), ax, [tz(z)], ang, (0, -1, 0), 0.25)[0])
    Vl.append(fold_ring(Vl[-1], ax.pos(tz(SHORTS_HEM_Z)), 0.10, (0, 0, 0.012)))
    Vl = np.array(Vl); Vr = Vl*np.array([-1, 1, 1])
    parts.append(Part('shorts_leg_L', 'kit', KIT_RECT['shorts_leg_L'], Vl, group='shorts'))
    parts.append(Part('shorts_leg_R', 'kit', KIT_RECT['shorts_leg_R'], Vr, group='shorts'))
    return parts


# ---------------------------------------------------------------- skeleton and skin weights
ARM_L1 = 0.295; ARM_L2 = 0.255


def bones():
    """[(name, head, tail, parent)] in armature space (rest pose). Left = +X."""
    B = [('Root', (0, 0, 0), (0, 0.10, 0), None), ('Hips', J['Hips'], J['Spine'], 'Root'), ('Spine', J['Spine'], J['Chest'], 'Hips'), ('Chest', J['Chest'], J['Neck'], 'Spine'),
         ('Neck', J['Neck'], J['Head'], 'Chest'), ('Head', J['Head'], J['HeadEnd'], 'Neck')]
    for sgn, t in ((1, 'L'), (-1, 'R')):
        m = np.array([sgn, 1, 1])
        B += [('Shoulder_' + t, J['Shoulder']*m, J['UpperArm']*m, 'Chest'), ('UpperArm_' + t, J['UpperArm']*m, J['LowerArm']*m, 'Shoulder_' + t),
              ('LowerArm_' + t, J['LowerArm']*m, J['Hand']*m, 'UpperArm_' + t), ('Hand_' + t, J['Hand']*m, J['HandEnd']*m, 'LowerArm_' + t),
              ('UpperLeg_' + t, J['UpperLeg']*m, J['LowerLeg']*m, 'Hips'), ('LowerLeg_' + t, J['LowerLeg']*m, J['Foot']*m, 'UpperLeg_' + t),
              ('Foot_' + t, J['Foot']*m, J['Toes']*m, 'LowerLeg_' + t), ('Toes_' + t, J['Toes']*m, J['ToesEnd']*m, 'Foot_' + t)]
    return [(n, tuple(map(float, h)), tuple(map(float, t)), p) for n, h, t, p in B]


def _norm(w):
    w = {k: float(v) for k, v in w.items() if v > 1e-4}; t = sum(w.values())
    w = dict(sorted(w.items(), key=lambda kv: -kv[1])[:4]); t = sum(w.values())
    return {k: v/t for k, v in w.items()}


def shorts_weights(p):
    """Position-only rule so welded duplicates (pelvis ring / leg ring) get identical weights."""
    x, y, z = p; side = 'L' if x >= 0 else 'R'
    wl = float(smoothstep(0.93, 0.79, z)*max(smoothstep(0.012, 0.070, abs(x)), smoothstep(0.826, 0.790, z)))     # below the crotch every vertex belongs to its leg
    return _norm({'Hips': 1 - wl, 'UpperLeg_' + side: wl})


def part_weights(part, verts):
    """Per-vertex weight dicts for one Part (verts in the order returned by Part.mesh)."""
    name = part.name; out = []; side = name[-1] if name[-2:] in ('_L', '_R') else None
    R, C = part.V.shape[:2]
    for i, p in enumerate(verts):
        x, y, z = p; ring = min(i//C, R - 1) if i < R*C else (R - 1 if part.pole_end is not None and i == R*C else 0)
        if name == 'torso':
            wh = 1 - float(smoothstep(0.93, 1.03, z)); wc = float(smoothstep(1.13, 1.25, z)); ws = 1 - wh - wc
            sd = 'L' if x >= 0 else 'R'
            clav = 0.65*float(smoothstep(0.09, 0.17, abs(x))*smoothstep(1.33, 1.41, z))
            wleg = 0.40*float(smoothstep(0.96, 0.87, z)*smoothstep(0.02, 0.10, abs(x)))
            w = {'Hips': wh*(1 - wleg), 'UpperLeg_' + sd: wh*wleg, 'Spine': ws, 'Chest': wc*(1 - clav), 'Shoulder_' + sd: wc*clav}
        elif name.startswith('sleeve'):
            w = {'UpperArm_' + side: 1.0}
        elif name.startswith('arm'):
            t = part.ring_t[ring] if i < R*C else part.ring_t[-1]
            wf = float(smoothstep(ARM_L1 - 0.050, ARM_L1 + 0.050, t)); whd = float(smoothstep(ARM_L1 + ARM_L2 - 0.020, ARM_L1 + ARM_L2 + 0.020, t))
            w = {'UpperArm_' + side: 1 - wf, 'LowerArm_' + side: wf*(1 - whd), 'Hand_' + side: wf*whd}
        elif name.startswith('leg'):
            wl = float(smoothstep(0.550, 0.460, z)); w = {'UpperLeg_' + side: 1 - wl, 'LowerLeg_' + side: wl}          # same rule as the sock: coincident skin / cloth move together
        elif name.startswith('sock'):
            wk = 1 - float(smoothstep(0.550, 0.460, z)); wf = float(smoothstep(0.150, 0.075, z)); w = {'UpperLeg_' + side: wk, 'LowerLeg_' + side: (1 - wk)*(1 - wf), 'Foot_' + side: wf}
        elif name.startswith('boot'):
            wf = float(smoothstep(0.150, 0.075, z)); wt = float(smoothstep(-0.085, -0.135, y)); w = {'LowerLeg_' + side: 1 - wf, 'Foot_' + side: wf*(1 - wt), 'Toes_' + side: wf*wt}
        elif name.startswith('shorts'):
            w = shorts_weights(p)
        else:
            raise KeyError(name)
        out.append(_norm(w))
    return out


def body_data():
    """Pure data for the whole body: verts, faces, per-loop uvs, per-face part name / material, per-vertex weights."""
    parts = build_parts(); verts = []; faces = []; uvs = []; fpart = []; fmat = []; weights = []; shorts_ids = []; info = {}
    for part in parts:
        base = len(verts); v, f, uv = part.mesh(base); w = part_weights(part, v)
        verts += v; faces += f; uvs += uv; fpart += [part.name]*len(f); fmat += [part.material]*len(f); weights += w
        info[part.name] = {'first': base, 'count': len(v), 'tris': sum(len(x) - 2 for x in f), 'material': part.material, 'rect': part.rect}
        if part.group == 'shorts':
            shorts_ids += list(range(base, base + len(v)))
    return {'verts': np.array(verts), 'faces': faces, 'uvs': np.array(uvs), 'face_part': fpart, 'face_material': fmat, 'weights': weights, 'shorts_ids': shorts_ids, 'info': info}
