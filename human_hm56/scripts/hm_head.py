"""HM56 head (from HM55; face detail and neck-to-shoulder transition added): original shape authored as a smooth union of ellipsoids / capsules (hm_sdf), sampled into a
ring x column quad grid from an inner axis. Head-local frame: origin = head pivot (top of the neck, between
the ears), Z up, face toward -Y, metres. The module includes the whole neck down to a hidden base ring that
sits inside the shirt collar, so there is no skin-to-skin seam between head and body.

Every number below is an authored design parameter (generic adult proportions); no mesh is read or traced."""
import math
import numpy as np
import hm_sdf as S
from hm_common import pchip, smoothstep

HEAD_TOP_Z = 0.160          # crown above the pivot
CHIN_Z = -0.065             # menton below the pivot  -> head height 0.225 m

# ---- shape parameters (P0 = neutral). Face variants override a few of these.
P0 = dict(
    cran_c=(0.0, 0.014, 0.076), cran_r=(0.0770, 0.0960, 0.0850),
    brow_c=(0.0, -0.040, 0.078), brow_r=(0.0650, 0.0560, 0.0600),      # forehead mass
    face_c=(0.0, -0.022, 0.012), face_r=(0.0660, 0.0740, 0.0820),      # face mask (cheek width, jaw taper)
    max_c=(0.0, -0.052, -0.024), max_r=(0.0360, 0.0420, 0.0400),       # maxilla / mouth region
    chin_c=(0.0, -0.0700, -0.0480), chin_r=(0.0240, 0.0240, 0.0195),
    gonion=(0.0390, -0.006, -0.033), jaw_tip=(0.0170, -0.0650, -0.0550), jaw_r1=0.0125, jaw_r2=0.0105,   # mandible border
    ramus_top=(0.0520, -0.006, 0.010), ramus_r=0.0120,
    cheek_c=(0.0500, -0.0580, 0.0220), cheek_r=(0.0180, 0.0200, 0.0140),
    ridge_y=-0.0930, ridge_z=0.0615, ridge_half=0.0420, ridge_r=0.0110, ridge_drop=0.004,
    nose_root=(0.0, -0.0900, 0.0500), nose_tip=(0.0, -0.1120, 0.0130), nose_r_root=0.0090, nose_r_tip=0.0105,
    tip_r=(0.0115, 0.0100, 0.0090),
    nose_base=(0.0, -0.1000, 0.0130), nose_base_r=(0.0125, 0.0150, 0.0125),      # solid wedge behind the tip (no undercut)
    ala=(0.0135, -0.1010, 0.0080), ala_r=(0.0080, 0.0095, 0.0070),
    lip_c=(0.0, -0.0860, -0.0196), lip_r=(0.0240, 0.0100, 0.0150),
    eye=(0.0320, -0.1000, 0.0440), eye_r=(0.0200, 0.0160, 0.0125), eye_k=0.010,
    neck_a=(0.0, 0.0330, -0.1500), neck_b=(0.0, 0.0110, -0.0150), neck_r1=0.0620, neck_r2=0.0555,
    larynx=(0.0, -0.0400, -0.0900), larynx_r=(0.0110, 0.0100, 0.0150),
    base_c=(0.0, 0.0240, -0.2000), base_r=(0.1000, 0.0640, 0.0400),    # skin under the collar opening (stays inside the shirt)
    k_skull=0.030, k_face=0.022, k_jaw=0.011, k_neck=0.012, k_nose=0.007, k_lip=0.008, k_cheek=0.018,
    # ---- HM56 face detail (design space, before the face scale)
    eyeball=(0.0320, -0.0890, 0.0442), eyeball_r=0.0118,
    lid_up=(0.0322, -0.0918, 0.0522), lid_up_r=(0.0145, 0.0102, 0.0034), lid_lo=(0.0322, -0.0918, 0.0395), lid_lo_r=(0.0118, 0.0084, 0.0020),
    infraorb=(0.0310, -0.0825, 0.0315), infraorb_r=(0.0165, 0.0080, 0.0085),
    zyg=(0.0520, -0.0685, 0.0265), zyg_r=(0.0165, 0.0140, 0.0085), hollow=(0.0500, -0.0725, 0.0040), hollow_r=(0.0140, 0.0085, 0.0090),
    cheek_fat=(0.0330, -0.0790, -0.0040), cheek_fat_r=(0.0120, 0.0090, 0.0140),
    lip_up=(0.0085, -0.0915, -0.0150), lip_up_r=(0.0125, 0.0062, 0.0052), tubercle=(0.0, -0.0932, -0.0158), tubercle_r=(0.0058, 0.0048, 0.0038),
    lip_lo=(0.0, -0.0905, -0.0245), lip_lo_r=(0.0165, 0.0064, 0.0058), mouth_z=-0.0196, mouth_half=0.0225,
    philtrum=(0.0042, -0.0925, -0.0085), philtrum_r=(0.0024, 0.0030, 0.0055),
    sulcus=(0.0, -0.0905, -0.0345), sulcus_r=(0.0130, 0.0042, 0.0042), mental=(0.0, -0.0895, -0.0475), mental_r=(0.0135, 0.0085, 0.0105),
    # ---- HM56 neck: sternocleidomastoid and the trapezius flare into the shoulders (unscaled, hidden part below the collar)
    scm_top=(0.0480, 0.0080, -0.0080), scm_bot=(0.0130, -0.0400, -0.1250), scm_r=(0.0085, 0.0080),
    trap_top=(0.0280, 0.0480, -0.0550), trap_bot=(0.0780, 0.0400, -0.1240), trap_r=(0.0150, 0.0160),
    scale=(1.10, 1.10, 1.10),                                          # skull/face scale about the pivot (neck and collar plug unscaled)
)


def mirror(c):
    return (-c[0], c[1], c[2])


def head_sdf(P):
    """Returns f(points (N,3)) -> signed distance (negative inside)."""
    sx, sy, sz = P['scale']
    def f(p):
        p = np.asarray(p, float)
        q = p/np.array([sx, sy, sz])                                   # scaled design space (neck/base are not scaled)
        d = S.ellipsoid(q, P['cran_c'], P['cran_r'])
        d = S.smin(d, S.ellipsoid(q, P['brow_c'], P['brow_r']), P['k_skull'])
        d = S.smin(d, S.ellipsoid(q, P['face_c'], P['face_r']), P['k_face'])
        d = S.smin(d, S.ellipsoid(q, P['max_c'], P['max_r']), P['k_face'])
        d = S.smin(d, S.ellipsoid(q, P['chin_c'], P['chin_r']), P['k_jaw'])
        for sgn in (1, -1):
            m = lambda c: (sgn*c[0], c[1], c[2])
            d = S.smin(d, S.round_cone(q, m(P['gonion']), m(P['jaw_tip']), P['jaw_r1'], P['jaw_r2']), P['k_jaw'])
            d = S.smin(d, S.round_cone(q, m(P['gonion']), m(P['ramus_top']), P['jaw_r1'], P['ramus_r']), P['k_jaw'])
            d = S.smin(d, S.ellipsoid(q, m(P['cheek_c']), P['cheek_r']), P['k_cheek'])
            a = (sgn*P['ridge_half'], P['ridge_y'] + 0.008, P['ridge_z'] - P['ridge_drop']); b = (sgn*0.007, P['ridge_y'], P['ridge_z'])
            d = S.smin(d, S.round_cone(q, a, b, P['ridge_r']*0.8, P['ridge_r']), 0.012)
        for sgn in (1, -1):                                            # eye sockets are carved before the nose so the bridge stays sharp
            e = P['eye']; d = S.smax(d, -S.ellipsoid(q, (sgn*e[0], e[1], e[2]), P['eye_r']), P['eye_k'])
        d = S.smin(d, S.round_cone(q, P['nose_root'], P['nose_tip'], P['nose_r_root'], P['nose_r_tip']), P['k_nose'])
        d = S.smin(d, S.ellipsoid(q, P['nose_tip'], P['tip_r']), 0.004)
        d = S.smin(d, S.ellipsoid(q, P['nose_base'], P['nose_base_r']), 0.006)
        for sgn in (1, -1):
            a = P['ala']; d = S.smin(d, S.ellipsoid(q, (sgn*a[0], a[1], a[2]), P['ala_r']), 0.004)
        d = S.smin(d, S.ellipsoid(q, P['lip_c'], P['lip_r']), P['k_lip'])
        if 'eyeball' in P:                                             # HM56 detail
            m2 = lambda c, sg: (sg*c[0], c[1], c[2])
            for sg in (1, -1):
                d = S.smin(d, np.linalg.norm(q - np.array(m2(P['eyeball'], sg)), axis=-1) - P['eyeball_r'], 0.0015)
                d = S.smin(d, S.ellipsoid(q, m2(P['lid_up'], sg), P['lid_up_r']), 0.0020)
                d = S.smin(d, S.ellipsoid(q, m2(P['lid_lo'], sg), P['lid_lo_r']), 0.0018)
                d = S.smin(d, S.ellipsoid(q, m2(P['zyg'], sg), P['zyg_r']), 0.012)
                if 'infraorb' in P:                                    # fills the trough under the lower lid (read as dark bags)
                    d = S.smin(d, S.ellipsoid(q, m2(P['infraorb'], sg), P['infraorb_r']), 0.010)
                d = S.smin(d, S.ellipsoid(q, m2(P['cheek_fat'], sg), P['cheek_fat_r']), 0.008)
                d = S.smin(d, S.ellipsoid(q, m2(P['lip_up'], sg), P['lip_up_r']), 0.0035)
                d = S.smin(d, S.ellipsoid(q, m2(P['philtrum'], sg), P['philtrum_r']), 0.0025)
                d = S.smax(d, -(np.linalg.norm(q - np.array([sg*P['mouth_half'], P['lip_c'][1] - 0.0010, P['mouth_z']]), axis=-1) - 0.0030), 0.0030)   # mouth corners
            d = S.smin(d, S.ellipsoid(q, P['tubercle'], P['tubercle_r']), 0.0030)
            d = S.smin(d, S.ellipsoid(q, P['lip_lo'], P['lip_lo_r']), 0.0035)
            d = S.smax(d, -S.ellipsoid(q, (0.0, P['lip_c'][1] - 0.008, P['mouth_z']), (P['mouth_half'], 0.0060, 0.0011)), 0.0018)       # mouth line
            d = S.smax(d, -S.ellipsoid(q, P['sulcus'], P['sulcus_r']), 0.0060)
            d = S.smin(d, S.ellipsoid(q, P['mental'], P['mental_r']), 0.008)
        d = d*min(sx, sy, sz)
        n = S.round_cone(p, P['neck_a'], P['neck_b'], P['neck_r1'], P['neck_r2'])
        n = S.smin(n, S.ellipsoid(p, P['larynx'], P['larynx_r']), 0.010)
        n = S.smin(n, S.ellipsoid(p, P['base_c'], P['base_r']), 0.030)
        if 'scm_top' in P:
            for sg in (1, -1):
                m3 = lambda c: (sg*c[0], c[1], c[2])
                n = S.smin(n, S.round_cone(p, m3(P['scm_top']), m3(P['scm_bot']), *P['scm_r']), 0.012)
                n = S.smin(n, S.round_cone(p, m3(P['trap_top']), m3(P['trap_bot']), *P['trap_r']), 0.022)
        return S.smin(d, n, P['k_neck'])
    return f


# ---- sampling grid (rings from the hidden base up to the crown pole; columns symmetric about the face)
THETA_HALF = [0, 3, 6, 9, 12, 15.5, 19, 23, 27.5, 32.5, 38, 44, 51, 59, 68, 78, 90, 103, 118, 136, 157, 180]     # degrees from the front (-Y) toward +X
RING_Z = [-0.196, -0.176, -0.160, -0.148, -0.138, -0.129, -0.121, -0.113, -0.105, -0.097, -0.089, -0.081, -0.072, -0.064, -0.0575, -0.0515, -0.0460, -0.0410, -0.0365, -0.0325, -0.0290,
          -0.0258, -0.0230, -0.0207, -0.0186, -0.0164, -0.0140, -0.0112, -0.0080, -0.0045, -0.0010, 0.0030, 0.0075, 0.0125, 0.0175, 0.0225,
          0.0275, 0.0320, 0.0360, 0.0395, 0.0420, 0.0445, 0.0470, 0.0495, 0.0525, 0.0560, 0.0610, 0.0670]
RING_PHI = [9, 19, 30, 42, 55, 68, 80]                # tilted rings from the cranium centre (degrees)
AXIS_Y = pchip([-0.200, -0.150, -0.080, -0.050, 0.000, 0.070], [0.030, 0.032, 0.018, 0.004, -0.004, 0.006])
CRAN_O = np.array([0.0, 0.006, 0.076])
BASE_RING_Z = RING_Z[0]


def thetas():
    h = THETA_HALF; return np.radians(np.array([-t for t in h[::-1][:-1]] + h[1:-1] + [180.0]) if False else np.array([-t for t in h[:0:-1]] + h[:-1]))


def grid_rays(sz=1.0):
    """rings: list of (origin, phi). columns: theta from -180 (exclusive duplicate of 180) ... +180-step; seam at the back."""
    th = np.radians(np.array([-t for t in THETA_HALF[-1:0:-1]] + THETA_HALF[:-1]))     # -180 .. +157 ; +180 == -180 (seam, back of head)
    zs = [z*sz if z > -0.078 else z for z in RING_Z]                                  # face rings follow the face scale
    rings = [(np.array([0.0, float(AXIS_Y(z)), z]), 0.0) for z in zs] + [(CRAN_O*np.array([1, 1, sz]), math.radians(a)) for a in RING_PHI]
    return th, rings


def sample(P):
    """Returns dict: V (R, C, 3) ring/column positions, pole (3,), theta (C,), ring params."""
    f = head_sdf(P); th, rings = grid_rays(P['scale'][2]); R, C = len(rings), len(th); cran_o = rings[-1][0]
    O = np.zeros((R, C, 3)); D = np.zeros((R, C, 3))
    for i, (o, phi) in enumerate(rings):
        O[i] = o; D[i, :, 0] = math.cos(phi)*np.sin(th); D[i, :, 1] = -math.cos(phi)*np.cos(th); D[i, :, 2] = math.sin(phi)
    t = S.outer_hit(f, O.reshape(-1, 3), D.reshape(-1, 3), 0.30)
    if np.isnan(t).any():
        raise ValueError('head ray missed the surface: %d rays' % int(np.isnan(t).sum()))
    V = (O.reshape(-1, 3) + D.reshape(-1, 3)*t[:, None]).reshape(R, C, 3)
    tp = S.outer_hit(f, cran_o[None], np.array([[0, 0, 1.0]]), 0.30)[0]
    V[:, :, 0] = np.where(np.abs(V[:, :, 0]) < 1e-9, 0.0, V[:, :, 0])
    return {'V': V, 'pole': cran_o + np.array([0, 0, tp]), 'theta': th, 'rings': rings, 'sdf': f}


def u_of_theta(th):
    """Texture u: the face (|theta| < 62 deg) gets 56 % of the width. theta in radians, -pi..pi -> 0..1."""
    a = np.degrees(np.asarray(th, float)); s = np.sign(a); a = np.abs(a)
    half = np.where(a <= 62, a/62*0.28, 0.28 + (a - 62)/118*0.22)
    return 0.5 + s*half


MAIN_V0, MAIN_V1 = 0.215, 0.995     # main chart occupies this v range of the head atlas; ears sit below


def build_mesh_data(P):
    """Grid -> vertices, quad faces, per-loop UVs. Columns wrap at the back seam (u 0 | 1)."""
    g = sample(P); V = g['V']; R, C = V.shape[:2]; th = g['theta']
    verts = [tuple(V[i, j]) for i in range(R) for j in range(C)] + [tuple(g['pole'])]
    vid = lambda i, j: i*C + (j % C); pole = R*C
    # v coordinate: cumulative length along the cheek meridian (column nearest 40 deg), then the pole
    jc = int(np.argmin(np.abs(np.degrees(th) - 40))); seg = np.linalg.norm(np.diff(V[:, jc], axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)]); total = cum[-1] + np.linalg.norm(g['pole'] - V[-1, jc])
    vrow = MAIN_V0 + (MAIN_V1 - MAIN_V0)*np.concatenate([cum, [total]])/total
    ucol = np.concatenate([u_of_theta(th), [1.0]]); ucol[0] = 0.0          # column C (wrap) = u 1
    faces = []; uvs = []
    for i in range(R - 1):
        for j in range(C):
            faces.append((vid(i, j), vid(i, j + 1), vid(i + 1, j + 1), vid(i + 1, j)))
            uvs += [(ucol[j], vrow[i]), (ucol[j + 1], vrow[i]), (ucol[j + 1], vrow[i + 1]), (ucol[j], vrow[i + 1])]
    for j in range(C):
        faces.append((vid(R - 1, j), vid(R - 1, j + 1), pole))
        uvs += [(ucol[j], vrow[R - 1]), (ucol[j + 1], vrow[R - 1]), ((ucol[j] + ucol[j + 1])/2, vrow[R])]
    return {'verts': np.array(verts), 'faces': faces, 'uvs': np.array(uvs), 'R': R, 'C': C, 'theta': th, 'vrow': vrow, 'ucol': ucol, 'grid': V, 'pole': g['pole'], 'sdf': g['sdf']}


# ---------------------------------------------------------------- ears (separate small shells, embedded at the root)
EAR = dict(root=(0.0, -0.010, 0.032), flare_deg=26.0, tilt=0.18, depth=0.0045,
           rim=[(0, 27), (7, 31), (16, 30.5), (24, 24), (28.5, 12), (28, -2), (24, -14), (16, -23), (8, -28.5), (2, -27), (0, -20)],   # (back, up) mm
           concha=(11.0, 1.0), inner_scale=0.52)
EAR_UV = {1: ((0.02, 0.02, 0.16, 0.20), (0.18, 0.02, 0.32, 0.20)), -1: ((0.34, 0.02, 0.48, 0.20), (0.50, 0.02, 0.64, 0.20))}   # (front rect, back rect) per side


def ear_data(sdf, sgn, E=EAR):
    """One ear (sgn = +1 character left / +X, -1 right). Returns verts, faces, per-loop uvs."""
    a = math.radians(E['flare_deg']); e_back = np.array([sgn*math.sin(a), math.cos(a), 0.0]); e_up = np.array([0.0, E['tilt'], 1.0]); e_up /= np.linalg.norm(e_up)
    n = np.cross(e_back, e_up); n = n if n[0]*sgn > 0 else -n                       # outward (lateral-forward) face normal
    # root point on the head surface at the tragus
    r0 = np.array(E['root']); t = S.outer_hit(sdf, r0[None], np.array([[float(sgn), 0, 0]]), 0.2)[0]; E0 = r0 + np.array([sgn*t, 0, 0]) - np.array([sgn*0.002, 0, 0])
    rim2 = np.array(E['rim'], float)/1000.0; c2 = np.array(E['concha'])/1000.0; K = len(rim2)
    rim = [E0 + e_back*b + e_up*u + n*(0.0015 if 0 < k < K - 1 else 0.0) for k, (b, u) in enumerate(rim2)]
    inner2 = c2 + (rim2 - c2)*E['inner_scale']
    inner = [E0 + e_back*b + e_up*u - n*E['depth']*0.6 for b, u in inner2]
    centre = E0 + e_back*c2[0] + e_up*c2[1] - n*E['depth']
    root = [E0 + e_back*(b*0.30) + e_up*(u*0.82) - np.array([sgn*0.004, 0, 0]) - n*0.004 for b, u in rim2]
    V = rim + inner + [centre] + root; iR = lambda k: k; iI = lambda k: K + k; iC = 2*K; iB = lambda k: 2*K + 1 + k
    (fu0, fv0, fu1, fv1), (bu0, bv0, bu1, bv1) = EAR_UV[sgn]
    def uvf(b, u):                                                                # front chart: back -> u, up -> v
        return (fu0 + (fu1 - fu0)*(0.08 + 0.84*b/0.030), fv0 + (fv1 - fv0)*(0.5 + 0.47*u/0.032))
    def uvb(b, u, k):
        return (bu0 + (bu1 - bu0)*(0.08 + 0.84*b/0.030), bv0 + (bv1 - bv0)*(0.5 + 0.47*u/0.032))
    faces = []; uvs = []
    flip = sgn < 0
    def add(idx, uv):
        if flip:
            idx = idx[::-1]; uv = uv[::-1]
        faces.append(tuple(idx)); uvs.extend(uv)
    for k in range(K - 1):
        add([iR(k), iR(k + 1), iI(k + 1), iI(k)], [uvf(*rim2[k]), uvf(*rim2[k + 1]), uvf(*inner2[k + 1]), uvf(*inner2[k])])
        add([iI(k), iI(k + 1), iC], [uvf(*inner2[k]), uvf(*inner2[k + 1]), uvf(*c2)])
        rb = rim2*np.array([0.30, 0.82])
        add([iR(k + 1), iR(k), iB(k), iB(k + 1)], [uvb(*rim2[k + 1], k), uvb(*rim2[k], k), uvb(*rb[k], k), uvb(*rb[k + 1], k)])
    # orientation check: front faces must look along +n
    Vn = np.array(V); f0 = faces[0]; nn = np.cross(Vn[f0[1]] - Vn[f0[0]], Vn[f0[2]] - Vn[f0[0]])
    if nn @ n < 0:
        faces = [f[::-1] for f in faces]; out = []; i = 0
        for f in faces:
            out.extend(uvs[i:i + len(f)][::-1]); i += len(f)
        uvs = out
    return {'verts': Vn, 'faces': faces, 'uvs': np.array(uvs), 'frame': {'E0': E0, 'e_back': e_back, 'e_up': e_up, 'n': n}, 'rim': np.array(rim)}


# ---------------------------------------------------------------- skin weights (Chest / Neck / Head)
NECK_BASE_Z = -0.110      # HM56: rigid with the chest up to just above the collar (-0.117), so the trapezius flare does not swing through the shirt


def face_sdf(P):
    """Skull + face only (no neck): used to keep the jaw rigid with the head."""
    Q = dict(P); f_all = head_sdf(P)
    sx, sy, sz = P['scale']
    def f(p):
        p = np.asarray(p, float); q = p/np.array([sx, sy, sz])
        d = S.ellipsoid(q, P['cran_c'], P['cran_r'])
        for c, r in (('brow_c', 'brow_r'), ('face_c', 'face_r'), ('max_c', 'max_r'), ('chin_c', 'chin_r')):
            d = S.smin(d, S.ellipsoid(q, P[c], P[r]), 0.02)
        for sgn in (1, -1):
            m = lambda c: (sgn*c[0], c[1], c[2])
            d = S.smin(d, S.round_cone(q, m(P['gonion']), m(P['jaw_tip']), P['jaw_r1'], P['jaw_r2']), 0.014)
            d = S.smin(d, S.round_cone(q, m(P['gonion']), m(P['ramus_top']), P['jaw_r1'], P['ramus_r']), 0.014)
        return d*min(sx, sy, sz)
    return f


def head_weights(P, verts):
    """verts in head-local coordinates. The plug below the collar follows the chest; the jaw follows the head."""
    ff = face_sdf(P); d = ff(np.asarray(verts, float)); out = []
    for (x, y, z), df in zip(verts, d):
        s_ = float(np.clip((z - NECK_BASE_Z)/0.093, 0, 1))
        wh = float(smoothstep(0.55, 1.0, s_)); wc = 1 - float(smoothstep(0.0, 0.40, s_))     # HM56: the Neck bone carries the middle of the neck
        face = float(smoothstep(0.020, 0.003, df))                 # 1 on the skull / jaw surface, fading over ~2 cm of throat under the jaw
        wh = max(wh, face); wc = min(wc, 1 - wh); wn = max(0.0, 1 - wh - wc)
        w = {k: v for k, v in (('Head', wh), ('Neck', wn), ('Chest', wc)) if v > 1e-4}; t = sum(w.values())
        out.append({k: v/t for k, v in w.items()})
    return out


# ---------------------------------------------------------------- scalp reference line (shared by texture and hair)
SCALP_C = (0.0, 0.014, 0.076)        # scalp analysis centre (scaled with the face scale)
# (azimuth from the front, elevation) of a natural short-hair hairline on this head: forehead, temple recess,
# sideburn in front of the ear, arc over the ear root, behind the ear down to the nape. Authored for this head.
SCALP_LINE = [(0, 27.0), (20, 27.5), (36, 25.0), (48, 19.0), (56, 7.0), (60.5, -12.0), (63, -24.0), (66.5, -25.0), (69.5, -10.0), (76, -7.0),
              (86, -7.5), (93, -10.0), (98, -22.0), (108, -36.0), (124, -44.0), (150, -50.0), (180, -52.0)]


def scalp_centre(P):
    return np.array(SCALP_C)*np.array(P['scale'])


def scalp_line_el(az_deg, line=None):
    pts = line or SCALP_LINE; f = pchip([a for a, _ in pts], [e for _, e in pts])
    return f(np.abs(np.asarray(az_deg, float)))


def azel_of(P, p):
    """Head-local points -> (azimuth 0..180 from the front, signed side, elevation) about the scalp centre."""
    q = np.asarray(p, float) - scalp_centre(P); r = np.linalg.norm(q, axis=-1)
    return np.degrees(np.arctan2(np.abs(q[..., 0]), -q[..., 1])), np.sign(q[..., 0]), np.degrees(np.arcsin(np.clip(q[..., 2]/np.maximum(r, 1e-9), -1, 1)))


# ---------------------------------------------------------------- face variants (shape overrides of P0)
def variant(**kw):
    q = dict(P0); q.update(kw); return q


FACES = {
    'P0': dict(name='NEUTRAL', intent_ja='基準の顔。', P=P0),
    'P1': dict(name='LONG_ANGULAR', intent_ja='面長で顎が角ばる。目は細く奥まり、眉骨が出る。鼻筋が長く高い。口は横に広く唇は薄い。',
               P=variant(scale=(1.075, 1.10, 1.150), gonion=(0.0430, -0.006, -0.0345), jaw_r1=0.0140, jaw_r2=0.0120, chin_r=(0.0275, 0.0245, 0.0200), jaw_tip=(0.0200, -0.0650, -0.0555),
                         ridge_r=0.0125, ridge_y=-0.0945, eye=(0.0315, -0.0985, 0.0440), eye_r=(0.0195, 0.0165, 0.0110), nose_root=(0.0, -0.0915, 0.0500), nose_tip=(0.0, -0.1150, 0.0115),
                         nose_r_root=0.0098, nose_r_tip=0.0105, ala=(0.0128, -0.1015, 0.0070), lip_r=(0.0275, 0.0115, 0.0125), cheek_r=(0.0170, 0.0190, 0.0130), k_jaw=0.011)),
    'P2': dict(name='ROUND_SOFT', intent_ja='丸顔。目は大きく間隔が広い。鼻は短く先が丸い。口は小さく唇は厚い。頬がふっくらしている。',
               P=variant(scale=(1.150, 1.10, 1.060), face_r=(0.0680, 0.0740, 0.0820), cheek_c=(0.0490, -0.0600, 0.0170), cheek_r=(0.0215, 0.0225, 0.0185), gonion=(0.0400, -0.006, -0.0320),
                         jaw_r1=0.0140, jaw_r2=0.0120, k_jaw=0.022, chin_c=(0.0, -0.0690, -0.0465), chin_r=(0.0225, 0.0225, 0.0185), eye=(0.0335, -0.1005, 0.0440), eye_r=(0.0210, 0.0160, 0.0135),
                         nose_root=(0.0, -0.0895, 0.0480), nose_tip=(0.0, -0.1105, 0.0160), nose_r_tip=0.0115, tip_r=(0.0125, 0.0105, 0.0098), ala=(0.0140, -0.1010, 0.0095), ala_r=(0.0085, 0.0095, 0.0072),
                         lip_r=(0.0245, 0.0130, 0.0165), ridge_r=0.0095, max_r=(0.0370, 0.0420, 0.0400))),
    'P3': dict(name='NARROW_SHARP', intent_ja='細面で顎が尖る。切れ長でやや上がった目、間隔は狭い。鼻は細く高い。頬骨が高い。',
               P=variant(scale=(1.045, 1.10, 1.125), face_r=(0.0625, 0.0740, 0.0820), cheek_c=(0.0480, -0.0590, 0.0260), cheek_r=(0.0180, 0.0195, 0.0130), gonion=(0.0360, -0.006, -0.0325),
                         jaw_r1=0.0115, jaw_r2=0.0095, chin_c=(0.0, -0.0705, -0.0500), chin_r=(0.0190, 0.0225, 0.0210), jaw_tip=(0.0140, -0.0660, -0.0570), eye=(0.0305, -0.0995, 0.0445),
                         eye_r=(0.0195, 0.0158, 0.0112), nose_root=(0.0, -0.0920, 0.0500), nose_tip=(0.0, -0.1165, 0.0130), nose_r_root=0.0078, nose_r_tip=0.0092, tip_r=(0.0098, 0.0095, 0.0085),
                         ala=(0.0118, -0.1010, 0.0078), ala_r=(0.0070, 0.0088, 0.0064), lip_r=(0.0255, 0.0118, 0.0135), k_jaw=0.012)),
}


def neck_sdf(P=None):
    """HM56: the unscaled neck block alone (neck cylinder, larynx, collar plug, SCM, trapezius) - used by the shirt
    so its yoke wraps the neck base at a constant distance."""
    P = P or P0
    def f(p):
        p = np.asarray(p, float); n = S.round_cone(p, P['neck_a'], P['neck_b'], P['neck_r1'], P['neck_r2'])
        n = S.smin(n, S.ellipsoid(p, P['larynx'], P['larynx_r']), 0.010); n = S.smin(n, S.ellipsoid(p, P['base_c'], P['base_r']), 0.030)
        for sg in (1, -1):
            m3 = lambda c: (sg*c[0], c[1], c[2])
            n = S.smin(n, S.round_cone(p, m3(P['scm_top']), m3(P['scm_bot']), *P['scm_r']), 0.012)
            n = S.smin(n, S.round_cone(p, m3(P['trap_top']), m3(P['trap_bot']), *P['trap_r']), 0.022)
        return n
    return f
