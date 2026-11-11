"""HM55 procedural textures. No input image is read: every texel is computed from the model's own geometry
(position / normal maps rasterised through its UVs), authored colour parameters and seeded numpy noise.
Head, neck, arms and legs all take their base colour from the same skin_base(tone) so they match by construction."""
import math
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- colour definitions (sRGB 0..1)
SKIN_TONES = {'T1': (0.865, 0.690, 0.560), 'T2': (0.800, 0.615, 0.480), 'T3': (0.715, 0.530, 0.400), 'T4': (0.900, 0.735, 0.625)}
KITS = {'A': dict(shirt=(0.93, 0.93, 0.91), trim=(0.07, 0.13, 0.33), shorts=(0.07, 0.13, 0.33), shorts_trim=(0.93, 0.93, 0.91), socks=(0.93, 0.93, 0.91), sock_trim=(0.07, 0.13, 0.33), boots=(0.07, 0.07, 0.08), boot_trim=(0.80, 0.80, 0.78), sleeve=(0.07, 0.13, 0.33), cuff=(0.93, 0.93, 0.91)),
        'B': dict(shirt=(0.86, 0.33, 0.10), trim=(0.12, 0.12, 0.14), shorts=(0.12, 0.12, 0.14), shorts_trim=(0.86, 0.33, 0.10), socks=(0.86, 0.33, 0.10), sock_trim=(0.12, 0.12, 0.14), boots=(0.10, 0.10, 0.11), boot_trim=(0.85, 0.85, 0.80), sleeve=(0.12, 0.12, 0.14), cuff=(0.86, 0.33, 0.10))}


def skin_base(tone):
    return np.array(SKIN_TONES[tone], float)


def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a)/(b - a), 0.0, 1.0)
    return t*t*(3 - 2*t)


def mix(a, b, t):
    t = np.asarray(t, float)[..., None] if np.ndim(t) == np.ndim(a) - 1 else t
    return a*(1 - t) + b*t


# ---------------------------------------------------------------- deterministic value noise on 3D points
def _hash(ix, iy, iz, seed):
    h = (ix*374761393 + iy*668265263 + iz*2147483647 + seed*1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13))*1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF)/65535.0


def noise3(p, freq, seed=0):
    q = np.asarray(p, float)*freq; i = np.floor(q).astype(np.int64); f = q - i; f = f*f*(3 - 2*f); out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0])*(f[..., 1] if dy else 1 - f[..., 1])*(f[..., 2] if dz else 1 - f[..., 2])
                out = out + w*_hash(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def fbm(p, freq, octaves=4, seed=0):
    v = 0; a = 0.5; t = 0
    for o in range(octaves):
        v = v + a*noise3(p, freq*2**o, seed + 17*o); t += a; a *= 0.5
    return v/t


# ---------------------------------------------------------------- UV rasteriser -> position / normal / id maps
def vertex_normals(verts, faces):
    V = np.asarray(verts, float); N = np.zeros_like(V)
    for f in faces:
        for k in range(1, len(f) - 1):
            a, b, c = f[0], f[k], f[k + 1]; n = np.cross(V[b] - V[a], V[c] - V[a]); N[a] += n; N[b] += n; N[c] += n
    return N/np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def rasterize(verts, faces, uvs, size, face_ids=None):
    """Returns dict(pos (H,W,3), nrm (H,W,3), fid (H,W) int, mask (H,W) bool). uvs per loop in face order."""
    W = H = size; V = np.asarray(verts, float); Nv = vertex_normals(V, faces)
    pos = np.zeros((H, W, 3)); nrm = np.zeros((H, W, 3)); fid = np.full((H, W), -1, np.int32); mask = np.zeros((H, W), bool)
    li = 0
    for fi, f in enumerate(faces):
        uv = np.asarray(uvs[li:li + len(f)], float); li += len(f)
        for k in range(1, len(f) - 1):
            idx = (0, k, k + 1); P = V[[f[j] for j in idx]]; Nn = Nv[[f[j] for j in idx]]
            px = uv[list(idx), 0]*W - 0.5; py = (1 - uv[list(idx), 1])*H - 0.5
            x0, x1 = int(max(0, math.floor(px.min()) - 1)), int(min(W - 1, math.ceil(px.max()) + 1)); y0, y1 = int(max(0, math.floor(py.min()) - 1)), int(min(H - 1, math.ceil(py.max()) + 1))
            if x1 < x0 or y1 < y0:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); d = (py[1] - py[2])*(px[0] - px[2]) + (px[2] - px[1])*(py[0] - py[2])
            if abs(d) < 1e-12:
                continue
            w0 = ((py[1] - py[2])*(X - px[2]) + (px[2] - px[1])*(Y - py[2]))/d; w1 = ((py[2] - py[0])*(X - px[2]) + (px[0] - px[2])*(Y - py[2]))/d; w2 = 1 - w0 - w1
            ins = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
            if not ins.any():
                continue
            yy, xx = Y[ins], X[ins]; w = np.stack([w0[ins], w1[ins], w2[ins]], 1)
            pos[yy, xx] = w @ P; nrm[yy, xx] = w @ Nn; fid[yy, xx] = fi if face_ids is None else face_ids[fi]; mask[yy, xx] = True
    n = np.linalg.norm(nrm, axis=2, keepdims=True); nrm = nrm/np.maximum(n, 1e-9)
    return {'pos': pos, 'nrm': nrm, 'fid': fid, 'mask': mask}


def bleed(rgb, mask, steps=10):
    """Edge padding: copy colours outward from covered texels so bilinear filtering never samples empty space."""
    rgb = rgb.copy(); m = mask.copy()
    for _ in range(steps):
        acc = np.zeros_like(rgb); cnt = np.zeros(m.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sm = np.roll(m, (dy, dx), (0, 1)); sr = np.roll(rgb, (dy, dx), (0, 1)); acc += sr*sm[..., None]; cnt += sm
        new = (~m) & (cnt > 0); rgb[new] = acc[new]/cnt[new][:, None]; m |= new
    return rgb


def save_rgb(path, rgb, alpha=None):
    a = np.clip(rgb, 0, 1); img = (a*255 + 0.5).astype(np.uint8)
    if alpha is not None:
        img = np.dstack([img, (np.clip(alpha, 0, 1)*255 + 0.5).astype(np.uint8)])
    Image.fromarray(img, 'RGB' if alpha is None else 'RGBA').save(path)


def cloth(base, pos, nrm, seed, fold_dir=(0.3, 0.0, 1.0), strength=0.07):
    """Fabric: fine weave noise + soft elongated folds + mild top-light shading."""
    d = np.asarray(fold_dir, float); d /= np.linalg.norm(d); q = pos.copy(); q = q - (q @ d)[..., None]*d*0.85
    folds = fbm(q, 9.0, 3, seed) - 0.5; weave = noise3(pos, 420.0, seed + 5) - 0.5
    shade = 1.0 + folds*strength*2.2 + weave*0.035 + 0.06*nrm[..., 2]
    return np.clip(base*shade[..., None], 0, 1)


def skin_shade(base, pos, nrm, seed, redness=None):
    """Common skin treatment for head / neck / arms / legs (same function everywhere -> same colour)."""
    lo = fbm(pos, 14.0, 3, seed) - 0.5; fine = noise3(pos, 600.0, seed + 3) - 0.5
    c = base[None, None, :]*np.ones(pos.shape[:2] + (1,))
    c = c*(1.0 + lo[..., None]*0.045 + fine[..., None]*0.02)
    c = c*(1.0 + 0.05*nrm[..., 2:3])                                    # slightly lighter on up-facing surfaces
    if redness is not None:
        c = c*(1 - redness[..., None]*np.array([0.00, 0.10, 0.11]))
    return c


# ================================================================== body: kit atlas
def paint_kit(body, kit, size=1024, seed=11):
    """body = hm_body.body_data(). Returns (rgb (H,W,3), mask)."""
    import hm_body as hb
    faces = [f for f, m in zip(body['faces'], body['face_material']) if m == 'kit']
    names = sorted(set(n for n, m in zip(body['face_part'], body['face_material']) if m == 'kit')); ids = [names.index(n) for n, m in zip(body['face_part'], body['face_material']) if m == 'kit']
    li = 0; uvs = []
    for f, m in zip(body['faces'], body['face_material']):
        if m == 'kit':
            uvs += [tuple(u) for u in body['uvs'][li:li + len(f)]]
        li += len(f)
    r = rasterize(body['verts'], faces, uvs, size, ids); pos, nrm, fid, mask = r['pos'], r['nrm'], r['fid'], r['mask']
    K = {k: np.array(v, float) for k, v in KITS[kit].items()}; rgb = np.zeros((size, size, 3)); x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    def region(prefix):
        return np.isin(fid, [i for i, n in enumerate(names) if n.startswith(prefix)]) & mask
    # ---- shirt torso
    m = region('torso'); az = np.degrees(np.arctan2(np.abs(x), -(y - 0.012)))                      # 0 front .. 180 back
    c = cloth(K['shirt'], pos, nrm, seed)
    half = 13 + 13*smoothstep(1.30, 0.90, z); panel = (np.abs(az - 92) < half) & (z < 1.345)
    c = np.where(panel[..., None], cloth(K['trim'], pos, nrm, seed + 1), c)
    if 'sleeve' in K:                                                                          # HM57: raglan shoulder panel in the sleeve colour (team colours read at match distance)
        ax_ = np.abs(x); zl = 1.300 + np.clip((0.190 - ax_)/0.115, 0, 1)*0.130
        rag = (z > zl) & (ax_ > 0.058)
        c = np.where(rag[..., None], cloth(K['sleeve'], pos, nrm, seed + 1), c)
    ring = hb.collar_ring(np.arange(0, 360, 3.0)); from scipy.spatial import cKDTree
    dcol, _ = cKDTree(ring).query(pos.reshape(-1, 3)); dcol = dcol.reshape(pos.shape[:2])
    collar = (dcol < 0.019) & (z > ring[:, 2].min() - 0.022)                                   # HM56: band measured from the real collar ring
    c = np.where(collar[..., None], cloth(K['trim'], pos, nrm, seed + 2, strength=0.03), c)
    c = c*(1 - 0.10*smoothstep(hb.SHIRT_HEM_Z + 0.014, hb.SHIRT_HEM_Z + 0.004, z))[..., None]       # hem stitch
    rgb[m] = c[m]
    # ---- sleeves
    for sgn, t in ((1, 'L'), (-1, 'R')):
        m = region('sleeve_' + t); a0 = hb.J['UpperArm']*np.array([sgn, 1, 1]); dr = hb.ARM_DIR*np.array([sgn, 1, 1]); along = (pos - a0) @ dr
        c = cloth(K.get('sleeve', K['shirt']), pos, nrm, seed + 3, fold_dir=dr); cuff = along > hb.SLEEVE_LEN - 0.024
        c = np.where(cuff[..., None], cloth(K.get('cuff', K['trim']), pos, nrm, seed + 4, fold_dir=dr, strength=0.03), c); rgb[m] = c[m]
    # ---- shorts (pelvis + legs)
    m = region('shorts'); c = cloth(K['shorts'], pos, nrm, seed + 5)
    stripe = (np.abs(y - 0.008) < 0.013) & (np.abs(x) > 0.125) & (np.sign(x) == np.sign(nrm[..., 0]))
    c = np.where(stripe[..., None], cloth(K['shorts_trim'], pos, nrm, seed + 6, strength=0.03), c)
    hem = z < hb.SHORTS_HEM_Z + 0.014
    c = np.where(hem[..., None], cloth(K['shorts_trim'], pos, nrm, seed + 6, strength=0.03), c); rgb[m] = c[m]
    # ---- socks
    m = region('sock'); c = cloth(K['socks'], pos, nrm, seed + 7, strength=0.035); top = hb.SOCK_TOP_Z
    hoop = ((z < top - 0.006) & (z > top - 0.020)) | ((z < top - 0.028) & (z > top - 0.040)) | (z > top - 0.001)
    c = np.where(hoop[..., None], cloth(K['sock_trim'], pos, nrm, seed + 8, strength=0.03), c)
    rib = 1 + 0.03*np.sin(np.degrees(np.arctan2(y, np.abs(x) - 0.10))*0.9); c = c*rib[..., None]; rgb[m] = c[m]
    # ---- boots
    m = region('boot'); c = np.ones_like(pos)*K['boots']; c = c*(1 + 0.25*(fbm(pos, 60.0, 2, seed + 9) - 0.5))[..., None]
    sole = z < 0.013; c = np.where(sole[..., None], K['boot_trim']*0.55, c)
    lace = (nrm[..., 2] > 0.45) & (y < -0.020) & (y > -0.105) & (np.abs(np.abs(x) - 0.104) < 0.016) & (np.mod(-y, 0.017) < 0.0055)
    c = np.where(lace[..., None], K['boot_trim'], c)
    tongue = (nrm[..., 2] > 0.45) & (y < -0.020) & (y > -0.105) & (np.abs(np.abs(x) - 0.104) < 0.0035)
    c = np.where(tongue[..., None], K['boot_trim']*0.8, c)
    c = c*(0.92 + 0.16*np.clip(nrm[..., 2], 0, 1))[..., None]; rgb[m] = c[m]
    return rgb, mask


# ================================================================== body: skin atlas (arms, hands, legs)
def paint_body_skin(body, tone, size=512, seed=23):
    import hm_body as hb
    faces = [f for f, m in zip(body['faces'], body['face_material']) if m == 'skin']
    names = sorted(set(n for n, m in zip(body['face_part'], body['face_material']) if m == 'skin')); ids = [names.index(n) for n, m in zip(body['face_part'], body['face_material']) if m == 'skin']
    li = 0; uvs = []
    for f, m in zip(body['faces'], body['face_material']):
        if m == 'skin':
            uvs += [tuple(u) for u in body['uvs'][li:li + len(f)]]
        li += len(f)
    r = rasterize(body['verts'], faces, uvs, size, ids); pos, nrm, fid, mask = r['pos'], r['nrm'], r['fid'], r['mask']
    base = skin_base(tone); x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    red = np.zeros(mask.shape)
    for sgn in (1, -1):
        k = hb.J['LowerLeg']*np.array([sgn, 1, 1]); e = hb.J['LowerArm']*np.array([sgn, 1, 1])
        red += 0.55*np.exp(-(((pos - (k + np.array([0, -0.045, 0.0])))**2).sum(-1))/(2*0.030**2))          # knees
        red += 0.45*np.exp(-(((pos - (e + np.array([0, 0.035, 0.0])))**2).sum(-1))/(2*0.024**2))           # elbows
        h = hb.J['Hand']*np.array([sgn, 1, 1]); red += 0.30*np.exp(-(((pos - (h + hb.FORE_DIR*np.array([sgn, 1, 1])*0.10))**2).sum(-1))/(2*0.05**2))   # knuckles
    rgb = skin_shade(base, pos, nrm, seed, redness=np.clip(red, 0, 1))
    # finger separation lines on the mitten hands (object space, along the hand axis)
    for sgn, t in ((1, 'L'), (-1, 'R')):
        _, R = hb.hand_sdf(sgn); w = hb.J['Hand']*np.array([sgn, 1, 1]); q = (pos - w) @ R                 # (palm normal, across, along)
        for off in (-0.019, 0.001, 0.021):
            line = np.exp(-((q[..., 1] - off)/0.0022)**2)*smoothstep(0.088, 0.104, q[..., 2])*(np.abs(q[..., 0]) > 0.004)
            rgb = rgb*(1 - 0.45*line[..., None]*np.isin(fid, [names.index('arm_' + t)])[..., None])
    # muscle definition: darker groove between calf heads / along the quadriceps tendon (very soft)
    groove = np.exp(-((np.abs(x) - 0.098)/0.006)**2)*smoothstep(0.52, 0.60, z)*smoothstep(0.76, 0.66, z)*(nrm[..., 1] < -0.6)
    rgb = rgb*(1 - 0.08*groove[..., None])
    return rgb, mask


# ================================================================== head atlas (face, neck, scalp, ears)
TEX0 = dict(tone='T2', brow_color=(0.070, 0.050, 0.040), brow_thick=1.0, brow_arch=1.0, brow_tilt=0.0, brow_len=1.0, brow_gap=1.0,
            eye_w=15.2, eye_open=1.12, eye_tilt=4.0, iris=(0.20, 0.115, 0.065), double_lid=0.55, lash=1.05, under_eye=0.06,
            lip_color=(0.690, 0.420, 0.380), lip_w=24.0, upper_lip=1.0, lower_lip=1.0, mouth_curve=0.0,
            blush=0.25, stubble=0.0, moles=(), hair_tint=(0.050, 0.045, 0.042), scalp=0.90)


def paint_head(hd, T, size=1024, seed=37):
    """hd = hm_assemble.head_data(P). T = texture parameter dict. Returns (rgb, mask, raster maps)."""
    import hm_head as hh
    P = hd['P']; sx, sy, sz = P['scale']; reg = {'head': 0, 'ear_L': 1, 'ear_R': 2}
    r = rasterize(hd['verts'], hd['faces'], [tuple(u) for u in hd['uvs']], size, [reg[n] for n in hd['face_region']])
    pos, nrm, fid, mask = r['pos'], r['nrm'], r['fid'], r['mask']; x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    base = skin_base(T['tone']); front = smoothstep(-0.020, -0.060, y)
    # ---- skin with redness (cheeks, nose tip, chin, ears)
    red = np.zeros(mask.shape)
    for sgn in (1, -1):
        c = np.array([sgn*0.046*sx, -0.078*sy, 0.008*sz]); red += T['blush']*np.exp(-(((pos - c)/np.array([0.022, 0.03, 0.018]))**2).sum(-1)/2)
    red += 0.30*np.exp(-(((pos - np.array(P['nose_tip'])*np.array([sx, sy, sz]))/0.012)**2).sum(-1)/2)
    red += 0.22*(fid > 0)
    rgb = skin_shade(base, pos, nrm, seed, redness=np.clip(red, 0, 1))
    forehead = np.exp(-((z - 0.095*sz)/0.03)**2)*front; rgb = rgb*(1 + 0.035*forehead[..., None])
    # ---- stubble (jaw, chin, upper lip)
    if T['stubble'] > 0:
        ztop = (-0.012 + 0.050*smoothstep(0.030, 0.066, np.abs(x)/sx))*sz                 # beard line: low at the mouth, rising to the sideburn
        beard = smoothstep(ztop + 0.006, ztop - 0.008, z)*smoothstep(-0.092*sz, -0.066*sz, z)*smoothstep(0.016, -0.010, y)*(fid == 0)
        soul = 1 - 0.75*np.exp(-((x/0.016)**2 + ((z - (-0.034*sz))/0.008)**2))             # lighter patch under the lower lip
        mous = np.exp(-((z - (-0.007*sz))/0.0055)**2)*smoothstep(0.031, 0.018, np.abs(x))*front
        st = np.clip(np.maximum(beard*soul, mous*0.9), 0, 1)*T['stubble']*(0.70 + 0.6*noise3(pos, 900.0, seed + 9))
        rgb = mix(rgb, rgb*np.array([0.66, 0.68, 0.74]), np.clip(st*0.50, 0, 1))
    eye_c = np.array(P['eye'])*np.array([sx, sy, sz]); ex, ez = eye_c[0], eye_c[2]
    for sgn in (1, -1):
        a = (x - sgn*ex)*sgn*1000.0; b = (z - ez)*1000.0; near = (np.abs(a) < 30) & (np.abs(b) < 28) & (y < -0.03) & (fid == 0)
        # ---- brows
        a0, a1 = -16.0*T['brow_gap'], 20.5*T['brow_len']; s_ = np.clip((a - a0)/(a1 - a0), 0, 1)
        hb_ = 13.0*sz/1.06 + 3.0*T['brow_arch']*np.sin(np.clip(s_/0.62, 0, 1)*math.pi/2) - 3.4*T['brow_arch']*np.clip((s_ - 0.62)/0.38, 0, 1)**1.5 + T['brow_tilt']*(s_ - 0.35)*9.0
        th = 8.2*T['brow_thick']*(1 - 0.62*s_**1.4)*smoothstep(0.0, 0.06, s_)
        dens = smoothstep(th/2, th/2 - 1.6, np.abs(b - hb_))*((a > a0 - 0.5) & (a < a1))*near
        phi = math.radians(28); u1 = a*math.cos(phi) + b*math.sin(phi); u2 = -a*math.sin(phi) + b*math.cos(phi)
        strand = noise3(np.stack([u1/5.0, u2/0.42, np.full_like(u1, sgn*3.0)], -1), 1.0, seed + 21)
        dens = np.clip(dens*(0.50 + 0.75*strand), 0, 1)
        rgb = mix(rgb, np.array(T['brow_color'])*(0.9 + 0.3*strand[..., None]), dens*0.93)
        # ---- eye
        tau = math.tan(math.radians(T['eye_tilt'])); bt = b - a*tau; w_in, w_out = T['eye_w'], T['eye_w'] + 1.2
        t = np.where(a < 0, a/w_in, a/w_out); tt = np.clip(np.abs(t), 0, 1)
        up = 5.5*T['eye_open']*(1 - tt**2.3)**0.72; lo = -3.5*T['eye_open']*(1 - tt**2.0)**0.9
        inside = (np.abs(t) < 1) & (bt < up) & (bt > lo) & near
        edge = np.minimum(smoothstep(0, 0.9, up - bt), smoothstep(0, 0.7, bt - lo))*inside
        scl = np.array([0.905, 0.890, 0.875])*(1 - 0.26*smoothstep(up - 3.2, up, bt))[..., None]*(1 - 0.14*tt**3)[..., None]
        ia, ib = 0.2, 0.9*T['eye_open']; rr = np.sqrt((a - ia)**2 + (bt - ib)**2); iris_r = 5.9
        iris = np.array(T['iris'])*(1.25 - 0.55*smoothstep(iris_r*0.55, iris_r, rr))[..., None]*(0.80 + 0.45*smoothstep(1.5, -3.5, bt - ib))[..., None]
        eye = np.where((rr < iris_r)[..., None], iris, scl); eye = np.where((rr < 2.5)[..., None], np.array([0.02, 0.02, 0.025]), eye)
        eye = mix(eye, iris*0.55, smoothstep(iris_r - 0.9, iris_r, rr)*(rr < iris_r + 0.35)*0.8)                  # limbal ring
        cl = np.sqrt((a - (ia + sgn*1.9))**2 + (bt - (ib + 2.0))**2); eye = np.where((cl < 1.05)[..., None], np.array([0.98, 0.98, 0.98]), eye)
        rgb = mix(rgb, eye, edge)
        lash_t = (1.15 + 0.85*smoothstep(-0.4, 1.0, t))*T['lash']
        lash = np.exp(-((bt - up)/lash_t)**2)*(np.abs(t) < 1.07)*near
        rgb = mix(rgb, np.array([0.055, 0.04, 0.035]), np.clip(lash*0.95, 0, 1))
        low = np.exp(-((bt - lo)/0.55)**2)*(np.abs(t) < 1.0)*near; rgb = rgb*(1 - 0.30*low[..., None])
        crease = np.exp(-((bt - (up + 2.9 + 0.9*(1 - tt**2)))/0.55)**2)*(np.abs(t) < 0.98)*near; rgb = rgb*(1 - 0.38*T['double_lid']*crease[..., None])
        ue = np.exp(-((bt - (lo - 3.5))/3.0)**2)*np.exp(-(a/13.0)**2)*near; rgb = rgb*(1 - 0.10*T['under_eye']*ue[..., None]*np.array([0.8, 1.0, 1.0]))
    # ---- nostrils (only on the down-facing underside of the nose)
    ala = np.array(P['ala'])*np.array([sx, sy, sz])
    nost = (((np.abs(x) - 0.0060*sx)/0.0027)**2 + ((y - (ala[1] - 0.0015))/0.0044)**2)
    nmask = smoothstep(1.25, 0.6, nost)*smoothstep(ala[2] - 0.0005, ala[2] - 0.0040, z)*(z > ala[2] - 0.013*sz)*(fid == 0)
    rgb = mix(rgb, np.array([0.16, 0.08, 0.07]), np.clip(nmask, 0, 1)*0.80)
    # ---- lips
    mz = P['lip_c'][2]*sz + 0.0002; a = x*1000.0; b = (z - mz)*1000.0; w = T['lip_w']; t = np.clip(np.abs(a)/w, 0, 1.3)
    lipreg = (y < -0.05) & (np.abs(a) < w*1.25) & (np.abs(b) < 18) & (fid == 0)
    bm = T['mouth_curve']*2.6*t**2 - 0.25*(1 - t**2)
    bu = bm + T['upper_lip']*5.4*np.clip(1 - t**1.7, 0, 1)*(0.84 + 0.16*(1 - np.exp(-(a/2.8)**2)))
    bl = bm - T['lower_lip']*7.4*np.clip(1 - t**2.0, 0, 1)**0.8
    lc = np.array(T['lip_color'])
    upm = smoothstep(0, 0.8, bu - b)*smoothstep(0, 0.5, b - bm)*(t < 1)*lipreg; lom = smoothstep(0, 0.9, b - bl)*smoothstep(0, 0.5, bm - b)*(t < 1)*lipreg
    rgb = mix(rgb, lc*0.84, upm*0.92); hl = np.exp(-((b - (bm - 3.0*T['lower_lip']))/1.7)**2)*np.exp(-(a/9.0)**2)
    rgb = mix(rgb, lc*(1.0 + 0.13*hl[..., None]), lom*0.92)
    line = np.exp(-((b - bm)/0.55)**2)*smoothstep(1.06, 0.92, t)*lipreg; rgb = mix(rgb, np.array([0.26, 0.13, 0.12]), np.clip(line, 0, 1)*0.9)
    corner = np.exp(-(((np.abs(a) - w)/1.6)**2 + ((b - bm)/1.2)**2))*lipreg; rgb = rgb*(1 - 0.35*corner[..., None])
    below = np.exp(-((b - (bl - 2.2))/2.2)**2)*np.exp(-(a/11.0)**2)*lipreg; rgb = rgb*(1 - 0.07*below[..., None])
    # ---- moles
    for mxx, mzz, rad in T['moles']:
        dm = np.sqrt((x - mxx*sx)**2 + (z - mzz*sz)**2)*1000.0; rgb = mix(rgb, np.array([0.20, 0.12, 0.09]), smoothstep(rad, rad*0.5, dm)*front*0.9)
    # ---- scalp undercoat inside the reference hairline (so a lifted hair edge never shows bare skin)
    az, side, el = hh.azel_of(P, pos); line_el = hh.scalp_line_el(az)
    inside_el = el - (line_el + 3.0)                                              # 3 deg inside the reference line
    grain = fbm(pos, 260.0, 2, seed + 31)
    sc_ = smoothstep(-1.5, 3.5, inside_el + (grain - 0.5)*5.0)*(fid == 0)*T['scalp']
    hair = np.array(T['hair_tint'])*(0.85 + 0.9*noise3(pos, 700.0, seed + 33)[..., None])
    rgb = mix(rgb, mix(rgb*0.55, hair, 0.72), np.clip(sc_, 0, 1))
    # ---- ears: darker concha, lighter rim
    for sgn, k in ((1, 1), (-1, 2)):
        fr = hd['ears'][sgn]['frame']; q = pos - fr['E0']; eb = q @ fr['e_back']; eu = q @ fr['e_up']; dn = q @ fr['n']
        concha = np.exp(-(((eb - 0.011)/0.0075)**2 + ((eu - 0.001)/0.012)**2))*(fid == k)*(nrm @ fr['n'] > 0)
        rgb = rgb*(1 - 0.10*concha[..., None]*np.array([0.85, 1.0, 1.0]))
    return np.clip(rgb, 0, 1), mask, r


FACE_TEX = {
    'P0': dict(TEX0),
    'P1': dict(TEX0, tone='T3', brow_thick=1.28, brow_arch=0.35, brow_tilt=-0.10, brow_len=1.05, eye_open=0.80, eye_tilt=2.0, double_lid=0.15, under_eye=0.55, lip_w=26.0,
               upper_lip=0.72, lower_lip=0.80, lip_color=(0.600, 0.370, 0.330), blush=0.10, stubble=0.75),
    'P2': dict(TEX0, tone='T1', brow_thick=0.92, brow_arch=1.45, brow_len=0.95, eye_w=15.4, eye_open=1.20, eye_tilt=3.0, double_lid=0.95, lash=1.15, under_eye=0.15, lip_w=22.0,
               upper_lip=1.15, lower_lip=1.20, lip_color=(0.760, 0.440, 0.410), blush=0.55, iris=(0.24, 0.14, 0.08)),
    'P3': dict(TEX0, tone='T2', brow_thick=0.95, brow_arch=0.75, brow_tilt=0.42, brow_len=1.02, eye_w=14.8, eye_open=0.88, eye_tilt=8.5, double_lid=0.35, lash=1.2, lip_w=23.5,
               upper_lip=0.78, lower_lip=0.95, mouth_curve=0.35, blush=0.18, moles=((0.0405, 0.0275, 1.25),), iris=(0.16, 0.10, 0.06)),
}
