"""HM55 hair H1-H4 for the original HM55 head. Same construction idea as the FH53/FH54 generator (own code):
opaque scalp-hugging cap + alpha hairline band + strand cards, but every surface is measured against the HM55
head (analytic skull radius, HM55 ear shells). Head-local frame of hm_head. No FACE52 / Reference04 data is used:
hair volumes are authored thickness fields, hairlines are authored against hm_head.SCALP_LINE."""
import math
import numpy as np
import hm_sdf as S, hm_head as hh
from hm_common import smoothstep, pchip

R0, TILE = 0.10, 0.075                 # cap UV: v = theta*R0/TILE (one texture repeat ~ 75 mm)
CLEAR = 0.0008                         # minimum cap height above the skull at cap vertices
STRIPS = [(0, 128), (128, 256), (256, 384), (384, 448), (448, 512)]
FRINGE_ZMIN = 0.092                    # fringe tips stop above the brow zone (head-local z, face scale 1.10)
MAX_CARD_PUSH = 0.0025


def azel_to_dir(az_deg, el_deg):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return np.array([math.cos(e)*math.sin(a), -math.cos(e)*math.cos(a), math.sin(e)])


def dir_to_azel(d):
    d = np.asarray(d, float); d = d/np.linalg.norm(d, axis=-1, keepdims=True)
    return np.degrees(np.arctan2(d[..., 0], -d[..., 1])), np.degrees(np.arcsin(np.clip(d[..., 2], -1, 1)))


class PolarFrame:
    """Polar coordinates (theta from the pole axis, phi around it)."""
    def __init__(self, pole_dir, ref_dir):
        A = np.asarray(pole_dir, float); A /= np.linalg.norm(A); R = np.asarray(ref_dir, float); R = R - A*(R @ A); R /= np.linalg.norm(R)
        self.A, self.R, self.B = A, R, np.cross(A, R)

    def dir(self, theta, phi):
        theta = np.asarray(theta, float); phi = np.asarray(phi, float); st = np.sin(theta)[..., None]
        return np.cos(theta)[..., None]*self.A + st*(np.cos(phi)[..., None]*self.R + np.sin(phi)[..., None]*self.B)

    def polar(self, d):
        d = np.asarray(d, float); d = d/np.linalg.norm(d, axis=-1, keepdims=True)
        return np.arccos(np.clip(d @ self.A, -1, 1)), np.arctan2(d @ self.B, d @ self.R) % (2*np.pi)


class HeadField:
    """Radial description of the HM55 head about the scalp centre: skull (no ears) on a 1 degree grid from the
    head's own shape function, plus exact ray tests against the ear shells."""
    def __init__(self, hd, step=1.0):
        P = hd['P']; self.P = P; self.C = hh.scalp_centre(P); f = hd['grid']['sdf']
        naz, nel = int(round(360/step)), int(round(180/step)); self.step = step
        self.g_az = (np.arange(naz) + 0.5)*step - 180.0; self.g_el = (np.arange(nel) + 0.5)*step - 90.0
        AZ, EL = np.meshgrid(np.radians(self.g_az), np.radians(self.g_el))
        D = np.stack([np.cos(EL)*np.sin(AZ), -np.cos(EL)*np.cos(AZ), np.sin(EL)], -1).reshape(-1, 3)
        t = S.outer_hit(f, np.repeat(self.C[None], len(D), 0), D, 0.45, steps=120, iters=24)
        g = t.reshape(nel, naz); self.g_skull = np.where(np.isfinite(g), g, np.nanmax(g))
        V = hd['verts']; tris = []
        for fc_, reg in zip(hd['faces'], hd['face_region']):
            if reg != 'head':
                tris += [(fc_[0], fc_[k], fc_[k + 1]) for k in range(1, len(fc_) - 1)]
        self.ear_tri = V[np.array(tris)]                                     # (T, 3, 3)
        self.head_V = V; self.head_T = [(fc_[0], fc_[k], fc_[k + 1]) for fc_ in hd['faces'] for k in range(1, len(fc_) - 1)]

    def _grid(self, grid, d):
        az, el = dir_to_azel(d); x = (np.asarray(az) - self.g_az[0])/self.step; y = np.clip((np.asarray(el) - self.g_el[0])/self.step, 0, len(self.g_el) - 1.0001)
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0; n = len(self.g_az)
        g = lambda yy, xx: grid[yy, xx % n]
        return g(y0, x0)*(1 - fx)*(1 - fy) + g(y0, x0 + 1)*fx*(1 - fy) + g(y0 + 1, x0)*(1 - fx)*fy + g(y0 + 1, x0 + 1)*fx*fy

    def r_skull(self, d):
        return float(self._grid(self.g_skull, np.asarray(d, float)))

    def r_ear(self, d):
        """Outermost ear hit along the ray from the centre, or nan."""
        d = np.asarray(d, float); T = self.ear_tri; e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]; h = np.cross(d, e2); a = (e1*h).sum(1)
        ok = np.abs(a) > 1e-12; f = np.where(ok, 1/np.where(ok, a, 1), 0); s = self.C - T[:, 0]; u = f*(s*h).sum(1); q = np.cross(s, e1); v = f*(q @ d); t = f*(e2*q).sum(1)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        return float(t[hit].max()) if hit.any() else float('nan')

    def r_all(self, d):
        r = self.r_skull(d); e = self.r_ear(d)
        return max(r, e) if math.isfinite(e) else r

    def point(self, d, r):
        return self.C + np.asarray(d, float)*r


def surface_normal(C, rfun, d, eps=0.035):
    d = np.asarray(d, float); d = d/np.linalg.norm(d); t1 = np.cross(d, [0, 0, 1.0])
    if np.linalg.norm(t1) < 1e-6:
        t1 = np.cross(d, [1.0, 0, 0])
    t1 /= np.linalg.norm(t1); t2 = np.cross(d, t1)
    def Pt(v):
        v = v/np.linalg.norm(v); return C + v*rfun(v)
    n = np.cross(Pt(d + eps*t1) - Pt(d - eps*t1), Pt(d + eps*t2) - Pt(d - eps*t2)); n /= np.linalg.norm(n)
    return n if n @ d > 0 else -n


# ---------------------------------------------------------------- styles (all values authored for the HM55 head)
def _line(front):
    """Hairline = hm_head.SCALP_LINE with the forehead / temple part replaced by `front` [(az, el), ...] (az < 56)."""
    return list(front) + [p for p in hh.SCALP_LINE if p[0] >= 56]


STYLES = {
    'H1': dict(label='H1_STANDARD', intent_ja='標準的な短めの髪。前髪を額に少し下ろし、側面と襟足は自然な長さ。',
               pole=(180, 62), seam=(180, -30), K=8, noise_deg=0.6,
               line=_line([(0, 25.5), (20, 26.0), (36, 24.0), (48, 18.5)]),
               shell=dict(base_mm=9.5, edge_mm=0.9, band=0.26, bumps=[(0, 62, 60, 24, 8.5), (80, 28, 26, 20, 3.0), (-80, 28, 26, 20, 3.0), (180, 18, 55, 24, 3.5)]),   # HM57: more volume (reads at match distance)
               cards=[dict(name='fringe', az=(-50, 50), n=15, t_root=0.80, ext=lambda a: 24 + 8*min(1.0, abs(a)/40), w=17, strips=(1, 0, 2), segs=4, lift=0.06, jitter=5.0, drift=3.5, wvar=0.18),
                      dict(name='back', az=(112, 248), n=16, t_root=0.78, ext=lambda a: 15 + 10*math.cos(math.radians((a - 180)*1.3))**2, w=17, strips=(0, 2, 1), segs=4, lift=0.05, jitter=4.0, drift=2.5, wvar=0.15)]),
    'H2': dict(label='H2_SHORT_CROP', intent_ja='短髪。頭の丸みに沿う薄い毛量で、耳と襟足を出す。',
               pole=(180, 66), seam=(180, -30), K=8, noise_deg=1.0,
               line=_line([(0, 27.0), (20, 27.5), (36, 25.0), (48, 19.0)]),
               shell=dict(base_mm=4.2, edge_mm=0.7, band=0.45, side_cut=(58, 135, 30, 2.2)),
               cards=[dict(name='fringe_short', az=(-40, 40), n=12, t_root=0.86, ext=lambda a: 6, w=13, strips=(3,), segs=2, lift=0.10, jitter=1.5, drift=4.0)]),
    'H3': dict(label='H3_SWEPT_BACK', intent_ja='前髪を上げて後ろへ流す。額を出し、前頭部に高さを持たせ、側頭部は締める。',
               pole=(180, 80), seam=(180, -30), K=8, noise_deg=0.9, flow=dict(pole=(0, 12), seam_dir=(0.0, 0.0, -1.0), K=10),
               line=_line([(0, 29.5), (20, 30.0), (34, 29.5), (46, 23.0)]),
               shell=dict(base_mm=4.5, edge_mm=1.0, band=0.16, bumps=[(0, 55, 32, 15, 10.0), (0, 75, 60, 20, 3.0)], side_cut=(60, 130, 32, 2.5)),
               cards=[dict(name='front_sweep', mode='from_front', az=(-46, 46), n=15, t_entry=0.86, length=lambda a: 90 - 28*abs(a)/46, w=17, strips=(0, 2), segs=6, lift=0.0),
                      dict(name='mid_sweep', mode='from_front', az=(-34, 34), n=9, t_entry=0.66, length=lambda a: 66, w=17, strips=(2, 0), segs=5, lift=0.0, layer=2)]),
    'H4': dict(label='H4_SIDE_SWEPT_FRINGE', intent_ja='片分けの長め前髪。分け目から額を斜めに横切って流れ、側面と襟足は長め。',
               pole=(180, 62), seam=(180, -30), K=8, noise_deg=0.6, flow=dict(pole=(-42, 62), seam_dir=(0.6, 0.8, -0.2), K=8),
               line=_line([(0, 24.5), (20, 25.0), (36, 23.5), (48, 18.0)]),
               shell=dict(base_mm=8.0, edge_mm=1.0, band=0.22, bumps=[(55, 45, 35, 25, 5.0), (0, 65, 50, 22, 3.0), (180, 15, 60, 25, 3.0)]),
               cards=[dict(name='sweep_fringe', az=(-28, 54), n=13, t_root=0.55, ext=lambda a: 26 + 10*max(0.0, a)/54, w=16, strips=(0, 1, 2), segs=6, lift=0.04, jitter=3.0, drift=1.2, wvar=0.12),
                      dict(name='part_side', az=(-54, -34), n=3, t_root=0.70, ext=lambda a: 12, w=15, strips=(1, 0), segs=4, lift=0.05),
                      dict(name='back_long', az=(112, 248), n=16, t_root=0.74, ext=lambda a: 22 + 10*math.cos(math.radians((a - 180)*1.2))**2, w=18, strips=(0, 2, 1), segs=5, lift=0.05, jitter=4.0, drift=2.5, wvar=0.15)]),
}


def mirror_line(line):
    return list(line) + [(-a, e) for a, e in line if 0 < a < 180]


class HairBuilder:
    def __init__(self, hf, sid, spec):
        self.hf, self.sid, self.s = hf, sid, spec
        self.mesh_frame = PolarFrame(azel_to_dir(*spec['pole']), azel_to_dir(*spec['seam']))
        fl = spec.get('flow'); self.flow_frame = self.mesh_frame if fl is None else PolarFrame(azel_to_dir(*fl['pole']), fl['seam_dir'])
        self.K = spec['K'] if fl is None else fl['K']
        line = mirror_line(spec['line']); d = np.array([azel_to_dir(a, e) for a, e in line]); th, ph = self.mesh_frame.polar(d); o = np.argsort(ph); th, ph = th[o], ph[o]
        if np.any(np.diff(ph) < 1e-4):
            raise ValueError(f'{sid}: hairline not star-shaped around the pole')
        base = pchip(np.concatenate([ph - 2*np.pi, ph, ph + 2*np.pi]), np.concatenate([th, th, th]))
        amp = math.radians(spec.get('noise_deg', 0.0)); ph0 = {'H1': .3, 'H2': 1.1, 'H3': 2.0, 'H4': 2.9}.get(sid, 0.0)
        self.th_h = lambda p: base(np.asarray(p, float)) + amp*(0.55*np.sin(7*np.asarray(p, float) + ph0) + 0.30*np.sin(13*np.asarray(p, float) + 2*ph0) + 0.15*np.sin(23*np.asarray(p, float) + 3*ph0))
        self.line_phi = ph; self.shell = spec['shell']; self.cap_bvh = None

    def t_of(self, d):
        th, ph = self.mesh_frame.polar(d); return th/self.th_h(ph)

    def thickness_full(self, d):
        s = self.shell; T = s['base_mm']/1000; az, el = dir_to_azel(d); az = float(az); el = float(el)
        for a0, e0, sa, se, mm in s.get('bumps', []):
            da = (az - a0 + 180) % 360 - 180; T += mm/1000*math.exp(-0.5*((da/sa)**2 + ((el - e0)/se)**2))
        if 'side_cut' in s:
            a0, a1, emax, mm = s['side_cut']
            w = float(smoothstep(a0 - 10, a0 + 5, abs(az))*(1 - smoothstep(a1 - 5, a1 + 10, abs(az)))*(1 - smoothstep(emax - 10, emax + 5, el)))
            T = T*(1 - w) + mm/1000*w
        return T

    def r_shell(self, d, t=None):
        t = float(self.t_of(d)) if t is None else t; s = self.shell
        Sx = float(smoothstep(1.0, 1.0 - s['band'], t)); T = s['edge_mm']/1000 + (self.thickness_full(d) - s['edge_mm']/1000)*Sx
        return max(self.hf.r_skull(d) + T, self.hf.r_skull(d) + CLEAR)

    def set_cap_mesh(self, V, tris):
        from mathutils.bvhtree import BVHTree
        self.cap_bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in tris], all_triangles=True, epsilon=0.0)

    def r_capmesh(self, d):
        from mathutils import Vector
        if self.cap_bvh is None:
            return float('nan')
        d = np.asarray(d, float); loc, n, i, dist = self.cap_bvh.ray_cast(Vector(self.hf.C + d*0.5), Vector(-d), 0.5)
        return float((np.array(loc) - self.hf.C) @ d) if loc is not None else float('nan')

    def r_surf(self, d):
        """Hair surface inside the hairline; skin (ears included) plus the edge height outside it."""
        t = float(self.t_of(d))
        if t <= 1.0:
            r = self.r_shell(d, t); rc = self.r_capmesh(d)
            return max(r, rc) if math.isfinite(rc) else r
        return self.hf.r_all(d) + self.shell['edge_mm']/1000

    # ------------------------------------------------------------ cap
    lite = False                  # HM57: mobile LOD = fewer cap rings / columns (the hairline band keeps its rings)

    def cap_columns(self):
        uni = np.linspace(0, 2*np.pi, 22 if self.lite else 46, endpoint=False); ctl = self.line_phi
        if self.lite:
            ctl = ctl[::2]
        mids = (ctl + np.roll(ctl, -1) + np.where(np.roll(ctl, -1) < ctl, 2*np.pi, 0))/2 % (2*np.pi)
        cols = np.sort(np.concatenate([uni, ctl, mids]) % (2*np.pi)); keep = [cols[0]]
        for c in cols[1:]:
            if c - keep[-1] > math.radians(5.5 if self.lite else 2.2):
                keep.append(c)
        if 2*np.pi - keep[-1] + keep[0] < math.radians(5.5 if self.lite else 2.2):
            keep.pop()
        return np.array(keep)

    def build_cap(self):
        rings = [0.0, 0.07, 0.16, 0.26, 0.36, 0.46, 0.56, 0.65, 0.73, 0.80, 0.86, 0.91, 0.95, 0.98, 1.0]
        if self.lite:
            rings = [0.0, 0.14, 0.32, 0.50, 0.66, 0.80, 0.91, 0.96, 1.0]
        cols = self.cap_columns(); nc = len(cols); pole = self.mesh_frame.A
        verts = [self.hf.point(pole, self.r_shell(pole, 0.0))]; tvals = [0.0]; dirs = [pole]
        for t in rings[1:]:
            for ph in cols:
                d = self.mesh_frame.dir(t*float(self.th_h(ph)), ph); verts.append(self.hf.point(d, self.r_shell(d, t))); tvals.append(t); dirs.append(d)
        vid = lambda ring, col: 1 + (ring - 1)*nc + (col % nc); faces = [(0, vid(1, c), vid(1, c + 1)) for c in range(nc)]
        for r in range(1, len(rings) - 1):
            for c in range(nc):
                faces.append((vid(r, c), vid(r + 1, c), vid(r + 1, c + 1), vid(r, c + 1)))
        verts = np.array(verts); dirs = np.array(dirs); tvals = np.array(tvals)
        fb = self.shell.get('fade_back', 0.895); colphi = np.zeros(len(verts)); colphi[1:] = np.tile(cols, len(rings) - 1)
        azv = np.abs(dir_to_azel(dirs)[0]); wb = smoothstep(100, 150, azv); f0 = np.minimum(0.895*(1 - wb) + fb*wb, 0.97); f0[0] = 1.0
        alpha = 1 - np.clip((tvals - f0)/(1.0 - f0), 0, 1); alpha = alpha*alpha*(3 - 2*alpha)
        self.K_EDGE = 26; ue = colphi/(2*np.pi)*self.K_EDGE; ve = np.clip((1.0 - tvals)/np.maximum(1.0 - f0, 1e-3), 0, 1)
        normals = np.array([surface_normal(self.hf.C, lambda dd: self.r_shell(dd), d) for d in dirs])
        thf, phf = self.flow_frame.polar(dirs); u = phf/(2*np.pi)*self.K; v = thf*R0/TILE
        return verts, faces, dict(alpha=alpha, normal=normals, u=u, v=v, t=tvals, cols=nc, ue=ue, ve=ve)

    # ------------------------------------------------------------ cards
    def march(self, phi_f, drift=0.0, th0=None, frame=None):
        frame = frame or self.flow_frame; ths = np.radians(np.arange(0.5, 178, 0.35)); ph = np.full_like(ths, phi_f)
        if drift and th0 is not None:
            ph = phi_f + drift*np.maximum(ths - th0, 0)
        D = frame.dir(ths, ph); T = np.array([float(x) for x in self.t_of(D)])
        return ths, D, T

    def phi_for_hairline_az(self, targets, frame=None):
        frame = frame or self.flow_frame; outward = float(self.t_of(frame.A)) < 1.0; phis = np.linspace(0, 2*np.pi, 721)[:-1]; azs = []; ok = []     # pole inside the cap -> cards run outward
        for ph in phis:
            ths, D, T = self.march(ph, frame=frame); k = np.argmax(T > 1.0) if outward else np.argmax(T <= 1.0); valid = (T > 1.0).any() if outward else (T <= 1.0).any()
            azs.append(float(dir_to_azel(D[k])[0]) if valid else np.nan); ok.append(valid)
        azs = np.array(azs); ok = np.array(ok); out = []
        for a in targets:
            diff = np.abs((azs - a + 180) % 360 - 180); diff[~ok] = np.inf; out.append(phis[int(np.argmin(diff))])
        return out

    def card(self, phi_f, row, a_deg, k):
        mode = row.get('mode', 'outward'); frame = self.mesh_frame if mode == 'mesh_outward' else self.flow_frame; outward = mode in ('outward', 'mesh_outward')
        layer = (self._card_counter % 5) + row.get('layer', 0); self._card_counter += 1
        h0 = 0.0007 + 0.00045*layer; h_root = 0.0005; lift = row.get('lift', 0.0)
        ths, D, T = self.march(phi_f, frame=frame)
        if outward:
            i0 = int(np.argmax(T >= row['t_root'])); ext = (row['ext'](a_deg) + row.get('jitter', 0.0)*math.sin(12.9898*k + 78.233*row['az'][0]))/1000
            if row.get('drift'):
                rate = math.radians(row['drift'])*math.sin(4.1*k + 1.3)/math.radians(30); ths, D, T = self.march(phi_f, drift=rate, th0=ths[i0], frame=frame)
        else:
            ii = np.where(T <= row['t_entry'])[0]
            if len(ii) == 0:
                return None
            i0 = int(ii[0])
        pts = []; s_acc = 0.0; prev = None; s_hl = None; arc = []
        for i in range(i0, len(ths)):
            d = D[i]; on = T[i] <= 1.0
            if not on and s_hl is None and outward:
                s_hl = s_acc
            s_off = 0.0 if s_hl is None else s_acc - s_hl
            h = h_root + (h0 - h_root)*float(smoothstep(0.0, 0.012, s_acc)) + lift*s_off
            p = self.hf.point(d, self.r_surf(d) + h)
            if prev is not None:
                s_acc += float(np.linalg.norm(p - prev))
            az, el = dir_to_azel(d)
            if abs(float(az)) < 62 and p[2] < FRINGE_ZMIN and p[1] < -0.05:
                break
            if math.isfinite(self.hf.r_ear(d)) and (s_hl is not None or not outward):
                break                                   # cards end at the ear rim instead of crossing the ear
            if outward and s_hl is not None and on:
                break
            pts.append(p); arc.append(s_acc); prev = p
            if outward and s_hl is not None and s_acc - s_hl >= ext:
                break
            if not outward and s_acc >= row['length'](a_deg)/1000:
                break
        pts = np.array(pts); arc = np.array(arc)
        if len(pts) < 3:
            return None
        n = row['segs']; L = arc[-1]; ss = np.linspace(0, L, n + 1); Cc = np.array([np.interp(ss, arc, pts[:, j]) for j in range(3)]).T
        rows_v = []; rows_n = []; w = row['w']/1000*(1 + row.get('wvar', 0.0)*math.sin(7.31*k + 2.1))
        for i in range(n + 1):
            tgt = Cc[min(i + 1, n)] - Cc[max(i - 1, 0)]; tgt /= np.linalg.norm(tgt); d = Cc[i] - self.hf.C; d /= np.linalg.norm(d)
            nrm = surface_normal(self.hf.C, self.r_surf, d); lat = np.cross(nrm, tgt); lat /= np.linalg.norm(lat)
            wi = w*(1 - 0.30*ss[i]/max(L, 1e-6)); hi = (Cc[i] - self.hf.C) @ d - self.r_surf(d); pair = []
            for sgn in (-1, 1):
                q = Cc[i] + sgn*lat*wi/2; dq = q - self.hf.C; rq = np.linalg.norm(dq); dq /= rq
                pair.append(self.hf.point(dq, max(rq, self.r_surf(dq) + max(hi, h_root))))
            rows_v.append(pair); rows_n.append(nrm)
        return dict(v=np.array(rows_v), n=np.array(rows_n), strip=row['strips'][k % len(row['strips'])], length=L, name=row['name'], layer=layer)

    def build_cards(self):
        cards = []; self._card_counter = 0
        for row in self.s['cards']:
            a0, a1 = row['az']; azs = list(np.linspace(a0, a1, row['n']))
            if row.get('mirror'):
                azs = azs + [-a for a in azs]
            phis = self.phi_for_hairline_az(azs, frame=self.mesh_frame if row.get('mode') == 'mesh_outward' else None)
            for k, (a, ph) in enumerate(zip(azs, phis)):
                c = self.card(ph, row, a, k)
                if c is not None:
                    cards.append(c)
        return cards


def _adjacency(tris):
    adj = {}
    for t in tris:
        for a in t:
            adj.setdefault(a, set()).update(t)
    return adj


def overlap_pass(V, tris, obstacles, C, step=0.0003, iters=40, smooth=False, max_push=None):
    """Push movable triangles radially outward until they no longer overlap the obstacle triangles
    (BVH triangle overlap, epsilon 0). max_push bounds the total push per vertex (no inflating the hair)."""
    from mathutils.bvhtree import BVHTree
    pushed = 0; remaining = 0; tot = np.zeros(len(V)); obs = [BVHTree.FromPolygons([tuple(v) for v in OV], [tuple(t) for t in OT], all_triangles=True, epsilon=0.0) for OV, OT in obstacles]
    adj = _adjacency(tris) if smooth else None
    for it in range(iters):
        bm = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in tris], all_triangles=True, epsilon=0.0); hit = set()
        for bo in obs:
            hit.update(i for i, j in bm.overlap(bo))
        remaining = len(hit)
        if not hit:
            break
        idx = {v for t in hit for v in tris[t]}
        if smooth:
            more = set()
            for v in idx:
                more |= adj.get(v, set())
            idx |= more
        if max_push is not None:
            idx = {v for v in idx if tot[v] + step <= max_push + 1e-12}
            if not idx:
                break
        for v in idx:
            d = V[v] - C; V[v] = V[v] + d/np.linalg.norm(d)*step; tot[v] += step
        pushed += len(idx)
    return {'iterations': it + 1, 'vertex_pushes': pushed, 'remaining_overlapping_triangles': remaining, 'max_push_mm': round(float(tot.max())*1000, 3)}


def build_hair_data(hd, sid, spec=None, lite=False):
    """Returns pure data for one hair on one head: verts (head-local), triangles, per-triangle material
    (0 cap opaque, 1 hairline band, 2 cards), per-loop uv / colour / normal, and a build record."""
    spec = spec or STYLES[sid]; hf = hd.get('_headfield') or HeadField(hd); hd['_headfield'] = hf; hb = HairBuilder(hf, sid, spec); hb.lite = lite; C = hf.C
    cv, cf, ca = hb.build_cap(); V = np.array(cv, float); tris = []; tri_mat = []; uv = []; col = []; nrm = []
    for f in cf:
        us = [ca['u'][i] for i in f]
        if len(f) == 3 and f[0] == 0:
            uu = us[1:]; uu = [uu[0], uu[1] + (hb.K if uu[1] < uu[0] - hb.K/2 else 0)]; us = [(uu[0] + uu[1])/2] + uu
        else:
            b0 = us[0]; us = [x + hb.K if x < b0 - hb.K/2 else (x - hb.K if x > b0 + hb.K/2 else x) for x in us]
        corner = [((u, ca['v'][i]), (1, 1, 1, ca['alpha'][i]), ca['normal'][i]) for i, u in zip(f, us)]
        ues = [ca['ue'][i] for i in f]; b0 = ues[0]; ues = [x + hb.K_EDGE if x < b0 - hb.K_EDGE/2 else (x - hb.K_EDGE if x > b0 + hb.K_EDGE/2 else x) for x in ues]
        for tri in ([(0, 1, 2)] if len(f) == 3 else [(0, 1, 2), (0, 2, 3)]):
            edge = any(corner[j][1][3] < 0.999 for j in tri); tris.append(tuple(f[j] for j in tri)); tri_mat.append(1 if edge else 0)
            for j in tri:
                uv.append((ues[j], ca['ve'][f[j]]) if edge else corner[j][0]); col.append(corner[j][1]); nrm.append(corner[j][2])
    ncap = len(tris)
    cap_overlap = overlap_pass(V, tris, [(hf.head_V, hf.head_T)], C, smooth=True, max_push=0.004)
    hb.set_cap_mesh(V, tris); cards = sorted(hb.build_cards(), key=lambda c: c['layer'])
    capV, capT = V.copy(), list(tris); cap_attrs = (list(tri_mat), list(uv), list(col), list(nrm))

    def emit(cards):
        VV = [capV]; TT = list(capT); MM, UU, CC, NN = [list(x) for x in cap_attrs]; info = []; base = len(capV)
        for ci, c in enumerate(cards):
            keep = c.get('keep', c['v'].shape[0]); rows = c['v'][:keep]; VV.append(rows.reshape(-1, 3)); sx0, sx1 = STRIPS[c['strip']]; u0, u1 = sx0/512 + 0.006, sx1/512 - 0.006
            for i in range(keep - 1):
                a, b = base + 2*i, base + 2*i + 1; cc, dd = base + 2*(i + 1) + 1, base + 2*(i + 1); va, vb = 1 - i/(keep - 1), 1 - (i + 1)/(keep - 1)
                q = [(a, (u0, va), i), (b, (u1, va), i), (cc, (u1, vb), i + 1), (dd, (u0, vb), i + 1)]
                for tri in ((0, 1, 2), (0, 2, 3)):
                    TT.append(tuple(q[j][0] for j in tri)); MM.append(2); info.append((ci, i, va, vb))
                    for j in tri:
                        UU.append(q[j][1]); CC.append((1, 1, 1, 1)); NN.append(c['n'][q[j][2]])
            base += 2*keep
        return np.vstack(VV), TT, MM, UU, CC, NN, info

    V, tris, tri_mat, uv, col, nrm, tinfo = emit(cards); trimmed = []; card_overlap = None
    if len(tris) > ncap:
        from mathutils.bvhtree import BVHTree
        card_tris = tris[ncap:]; sub = np.unique(np.array(card_tris).ravel()); remap = {int(v): k for k, v in enumerate(sub)}
        LV = V[sub].copy(); LT = [tuple(remap[v] for v in t) for t in card_tris]; L0 = LV.copy()
        card_overlap = overlap_pass(LV, LT, [(hf.head_V, hf.head_T), (capV, capT)], C, max_push=MAX_CARD_PUSH)
        mv = np.linalg.norm(LV - L0, axis=1); card_overlap['card_vertex_push_mm'] = {'max': round(float(mv.max())*1000, 3), 'p95': round(float(np.percentile(mv, 95))*1000, 3)}
        V[sub] = LV; base = len(capV)
        for c in cards:
            n = c['v'].shape[0]; c['v'] = V[base:base + 2*n].reshape(n, 2, 3).copy(); base += 2*n
        bs = BVHTree.FromPolygons([tuple(v) for v in hf.head_V], [tuple(t) for t in hf.head_T], all_triangles=True, epsilon=0.0)
        for it in range(4):
            bc = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in tris[ncap:]], all_triangles=True, epsilon=0.0); hit = {}
            for i, j in bc.overlap(bs):
                ci, seg, va, vb = tinfo[i]
                if vb < 1 - 0.22:
                    hit[ci] = min(hit.get(ci, 99), seg)
            if not hit:
                break
            for ci, seg in hit.items():
                keep = max(seg + 1, 2)
                if keep < cards[ci].get('keep', cards[ci]['v'].shape[0]):
                    cards[ci]['keep'] = keep; trimmed.append({'card': cards[ci]['name'], 'kept_rows': keep, 'of': int(cards[ci]['v'].shape[0])})
            V, tris, tri_mat, uv, col, nrm, tinfo = emit(cards)
        card_overlap['cards_trimmed_at_skin'] = trimmed
    tris2 = []; uv2 = []; col2 = []; nrm2 = []
    for k, t in enumerate(tris):
        Pt = V[list(t)]; gn = np.cross(Pt[1] - Pt[0], Pt[2] - Pt[0]); nn = np.mean(nrm[3*k:3*k + 3], axis=0); order = (0, 2, 1) if gn @ nn < 0 else (0, 1, 2)
        tris2.append(tuple(t[j] for j in order))
        for j in order:
            uv2.append(uv[3*k + j]); col2.append(col[3*k + j]); nrm2.append(nrm[3*k + j])
    info = {'hair_id': spec['label'], 'intent_ja': spec['intent_ja'], 'cap_triangles': ncap, 'cards': len(cards), 'card_triangles': len(tris) - ncap,
            'hairline_azel_controls': mirror_line(spec['line']), 'shell': dict(spec['shell']), 'cap_vs_head_overlap_pass': cap_overlap, 'card_overlap_pass': card_overlap,
            'edge_triangles': int(sum(1 for m in tri_mat if m == 1))}
    return {'verts': V, 'tris': tris2, 'tri_mat': tri_mat, 'uv': np.array(uv2), 'col': np.array(col2), 'nrm': np.array(nrm2), 'info': info}
