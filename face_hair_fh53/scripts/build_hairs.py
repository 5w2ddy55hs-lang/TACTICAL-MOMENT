"""FH53 hair candidates H1-H4, built as real Blender geometry on the FACE52 head frame.

Each hair = one mesh object 'REF09_Hair' (same object name/role as FACE52, so it can replace
FACE52's hair in any combination) with two materials:
  TMH53_<id>_Cap    scalp-conforming shell, hairline feathered by vertex alpha
  TMH53_<id>_Cards  strand cards marched along the style's flow field
Inputs: FACE52 native .blend (face + back-scalp skin, FACE52 cap only as a volume reference for
the skull proxy) and the two procedural textures from make_hair_textures.py.
FACE52 files are opened read-only and never saved.

Usage: python build_hairs.py [--only H1,H2] [--preview]
"""
import sys, os, math, json, argparse, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import bpy
import fh53_common as fc
from scipy.interpolate import PchipInterpolator

R0, TILE = 0.10, 0.075        # UV: v = theta*R0/TILE  (one texture repeat ~ 75 mm)
CLEAR = 0.0008                # minimum hair-above-skin clearance at cap vertices (model units)

# ------------------------------------------------------------------ style definitions
# Angles: az 0 = front(-Y), +90 = +X side (viewer's right in the front view), 180 = back; el above HEAD_CENTRE.
# Hairlines are listed for the +X half and mirrored unless 'asym' is given.
H1_LINE = [(0, 39), (25, 39), (45, 37), (57, 24), (64, 8), (70, -6), (76, -12), (81, -8), (85, 14), (95, 21),
           (106, 18), (114, 4), (124, -10), (150, -21), (180, -24)]
STYLES = {
    'H1': dict(
        label='H1_STANDARD_REBUILT',
        intent_ja='H0(FACE52)の輪郭を引き継ぐ標準形の作り直し。帽子状の縁・前髪V字・頭頂の角・耳前の段差・襟足の帯を構造から解消する狙い。',
        pole=(180, 62), seam=(180, -30), K=8, line=H1_LINE,
        shell=dict(kind='cap0', blur_deg=7.0, extra_mm=0.0, edge_mm=1.0, band=0.26,
                   bumps=[(78, 32, 26, 22, 3.0), (-78, 32, 26, 22, 3.0), (180, 22, 55, 22, 2.0)]),
        cards=[
            dict(name='fringe', az=(-52, 52), n=17, t_root=0.78, ext=lambda a: 24 + 10*min(1.0, abs(a)/40), w=17, strips=(1, 0, 2), segs=4, lift=0.07, jitter=6.0, drift=3.5, wvar=0.18),
            dict(name='temple', az=(55, 84), n=5, t_root=0.80, ext=lambda a: 17, w=14, strips=(1, 0), segs=4, lift=0.07, mirror=True),
            dict(name='back', az=(118, 242), n=18, t_root=0.76, ext=lambda a: 20 + 16*math.cos(math.radians((a-180)*1.4))**2, w=17, strips=(0, 2, 1), segs=4, lift=0.05, jitter=4.0, drift=2.5, wvar=0.15),
        ]),
    'H2': dict(
        label='H2_SHORT_CROP',
        intent_ja='短髪クロップ。頭の丸みに沿う薄い毛量、耳と襟足を出す。シルエットを最も小さく締め、耳前は短いもみあげだけにする。',
        pole=(180, 66), seam=(180, -30), K=8,
        line=[(0, 42), (22, 42), (40, 40), (52, 30), (60, 16), (66, 4), (72, -3), (79, 3), (84, 16), (95, 22),
              (108, 18), (116, 8), (124, 0), (134, -12), (155, -23), (180, -27)],
        shell=dict(kind='const', top_mm=3.6, side_mm=2.2, edge_mm=0.7, band=0.45, fade_back=0.70),
        cards=[
            dict(name='fringe_short', az=(-40, 40), n=12, t_root=0.86, ext=lambda a: 6, w=13, strips=(3,), segs=2, lift=0.10, jitter=1.5, drift=4.0),
        ]),
    'H3': dict(
        label='H3_SWEPT_BACK',
        intent_ja='前髪を上げて後ろへ流す型。額を出し、前頭部に高さ、側頭部は締める。毛流れは額側から後頭部へ。',
        pole=(180, 80), seam=(180, -30), K=8,
        flow=dict(pole=(0, 22), seam_dir=(0.0, 0.0, -1.0), K=10),
        line=[(0, 43), (20, 42), (35, 41), (48, 34), (58, 20), (65, 6), (72, -4), (80, 2), (85, 14), (95, 20),
              (107, 16), (115, 6), (124, -4), (150, -21), (180, -25)],
        shell=dict(kind='bumps', base_mm=4.5, edge_mm=1.0, band=0.16, fade_back=0.74,
                   bumps=[(0, 58, 32, 14, 10.0), (0, 75, 60, 20, 3.0)], side_cut=(60, 130, 35, 2.5)),
        cards=[
            dict(name='front_sweep', mode='from_front', az=(-50, 50), n=16, t_entry=0.94, length=lambda a: 95 - 30*abs(a)/50, w=17, strips=(0, 2), segs=6, lift=0.0),
            dict(name='mid_sweep', mode='from_front', az=(-38, 38), n=10, t_entry=0.72, length=lambda a: 70, w=17, strips=(2, 0), segs=5, lift=0.0, layer=2),
            dict(name='side_sweep', mode='from_front', az=(50, 68), n=3, t_entry=0.96, length=lambda a: 30, w=14, strips=(1,), segs=4, lift=0.0, mirror=True),
        ]),
    'H4': dict(
        label='H4_SIDE_SWEPT_FRINGE',
        intent_ja='片分けの長め前髪。分け目は向かって左（キャラクターの右）で、前髪は額を斜めに横切って向かって右へ流れる。側面の毛先は耳の上縁まで下り、襟足は長めに覆う左右非対称の形。',
        pole=(-42, 62), seam=(150, -40), K=8,
        line=[(0, 39), (25, 39), (45, 37), (57, 24), (64, 8), (70, -6), (76, -12), (82, -8), (86, 10), (95, 16),
              (106, 13), (114, 2), (124, -14), (150, -30), (180, -33)],
        shell=dict(kind='cap0', blur_deg=7.0, extra_mm=0.0, edge_mm=1.0, band=0.22, bumps=[(60, 45, 35, 25, 4.0)]),
        cards=[
            dict(name='sweep_fringe', az=(-30, 72), n=15, t_root=0.55, ext=lambda a: 34 + 10*max(0.0, a)/72, w=17, strips=(0, 1, 2), segs=6, lift=0.05, jitter=4.0, drift=2.0, wvar=0.15),
            dict(name='part_side', az=(-78, -36), n=4, t_root=0.70, ext=lambda a: 16, w=15, strips=(1, 0), segs=4, lift=0.05),
            dict(name='overear_R', az=(80, 112), n=4, t_root=0.78, ext=lambda a: 24, w=16, strips=(0, 2), segs=5, lift=0.07),
            dict(name='overear_L', az=(-112, -80), n=4, t_root=0.78, ext=lambda a: 20, w=16, strips=(0, 2), segs=5, lift=0.07),
            dict(name='back_long', az=(116, 244), n=16, t_root=0.74, ext=lambda a: 30 + 10*math.cos(math.radians((a-180)*1.2))**2, w=18, strips=(0, 2, 1), segs=5, lift=0.05, jitter=4.0, drift=2.5, wvar=0.15),
        ]),
}
FRINGE_ZMIN = 0.088     # card tips stop above the brow zone in front of the face (|az|<60)
FACE_FREE_ZONE_NOTE = 'Face variants are frozen above z=0.080 and in front of the ears; see build_faces.py.'


def mirror_line(line):
    pts = list(line) + [(-a, e) for a, e in line if 0 < a < 180]
    return pts


class HairBuilder:
    def __init__(self, hf, sid, spec):
        self.hf, self.sid, self.s = hf, sid, spec
        self.mesh_frame = fc.PolarFrame(fc.azel_to_dir(*spec['pole']), fc.azel_to_dir(*spec['seam']))
        fl = spec.get('flow')
        self.flow_frame = self.mesh_frame if fl is None else fc.PolarFrame(fc.azel_to_dir(*fl['pole']), fl['seam_dir'])
        self.K = spec['K'] if fl is None else fl['K']
        line = spec.get('asym_line') or mirror_line(spec['line'])
        d = np.array([fc.azel_to_dir(a, e) for a, e in line])
        th, ph = self.mesh_frame.polar(d)
        o = np.argsort(ph); th, ph = th[o], ph[o]
        if np.any(np.diff(ph) < 1e-4):
            raise ValueError(f'{sid}: hairline not star-shaped around pole')
        php = np.concatenate([ph - 2*np.pi, ph, ph + 2*np.pi]); thp = np.concatenate([th, th, th])
        self.th_h = PchipInterpolator(php, thp)
        self.line_phi = ph
        self.shell = spec['shell']

    # mesh-frame hairline fraction t of a direction
    def t_of(self, d):
        th, ph = self.mesh_frame.polar(d)
        return th/self.th_h(ph)

    def thickness_full(self, d):
        s = self.shell; hf = self.hf
        if s['kind'] == 'cap0':
            if not hasattr(self, '_capgrid'):
                from scipy.ndimage import gaussian_filter
                n = len(hf.g_az); sig = s['blur_deg']/(hf.g_az[1]-hf.g_az[0])
                base = gaussian_filter(np.pad(hf.g_base, ((0, 0), (n, n)), mode='wrap'), sig)[:, n:2*n] + hf.CAP_THICKNESS_ASSUMED
                self._capgrid = np.maximum(base - hf.g_scalp, 0.002)
            T = float(hf.sample_grid(self._capgrid, d)) + s.get('extra_mm', 0)/1000
        elif s['kind'] == 'const':
            az, el = fc.dir_to_azel(d)
            side = fc.smoothstep(55, 80, abs(float(az))) * (1 - fc.smoothstep(25, 45, float(el)))
            T = (s['top_mm']*(1-side) + s['side_mm']*side)/1000
        else:  # bumps
            T = s['base_mm']/1000
        az, el = fc.dir_to_azel(d); az = float(az); el = float(el)
        for (a0, e0, sa, se, mm) in s.get('bumps', []):
            da = (az - a0 + 180) % 360 - 180
            T += mm/1000*math.exp(-0.5*((da/sa)**2 + ((el-e0)/se)**2))
        if 'side_cut' in s:
            a0, a1, emax, mm = s['side_cut']
            w = fc.smoothstep(a0-10, a0+5, abs(az))*(1-fc.smoothstep(a1-5, a1+10, abs(az)))*(1-fc.smoothstep(emax-10, emax+5, el))
            T = T*(1-w) + mm/1000*w
        return T

    def r_shell(self, d, t=None):
        """Outer hair surface radius at direction d (inside the hairline)."""
        if t is None:
            t = float(self.t_of(d))
        s = self.shell
        S = float(fc.smoothstep(1.0, 1.0 - s['band'], t))      # 1 inside, 0 at hairline
        T = s['edge_mm']/1000 + (self.thickness_full(d) - s['edge_mm']/1000)*S
        r = self.hf.r_scalp(d) + T
        rs = self.hf.r_skin(d)
        if math.isfinite(rs):
            r = max(r, rs + CLEAR)
        return r

    def past_hairline(self, d):
        """Distance (model units, ~arc at R0) beyond the hairline along the mesh-frame meridian; 0 inside."""
        th, ph = self.mesh_frame.polar(np.asarray(d, float))
        return max(0.0, float(th - self.th_h(ph)))*R0

    def set_cap_mesh(self, V, tris):
        from mathutils.bvhtree import BVHTree
        self.cap_bvh = BVHTree.FromPolygons([tuple(v) for v in V[:max(max(t) for t in tris)+1]], [tuple(t) for t in tris], all_triangles=True, epsilon=0.0)

    def r_capmesh(self, d):
        from mathutils import Vector
        if not hasattr(self, 'cap_bvh'):
            return float('nan')
        d = np.asarray(d, float); loc, n, i, dist = self.cap_bvh.ray_cast(Vector(self.hf.Cn + d*0.5), Vector(-d), 0.5)
        return float((np.array(loc) - self.hf.Cn) @ d) if loc is not None else float('nan')

    def r_surf(self, d):
        """Hair surface inside the hairline, skin (+edge) outside it (continuous at the hairline).
        Once the cap mesh exists, the actual (clearance-pushed) cap is used where it is higher."""
        t = float(self.t_of(d))
        if t <= 1.0:
            r = self.r_shell(d, t); rc = self.r_capmesh(d)
            return max(r, rc) if math.isfinite(rc) else r
        rs = self.hf.r_skin(d)
        if not math.isfinite(rs):
            rs = self.hf.r_scalp(d)
        return rs + self.shell['edge_mm']/1000

    # ------------------------------------------------------------------ cap
    def cap_columns(self):
        uni = np.linspace(0, 2*np.pi, 46, endpoint=False)
        ctl = self.line_phi
        mids = (ctl + np.roll(ctl, -1) + np.where(np.roll(ctl, -1) < ctl, 2*np.pi, 0))/2 % (2*np.pi)
        cols = np.sort(np.concatenate([uni, ctl, mids]) % (2*np.pi))
        keep = [cols[0]]
        for c in cols[1:]:
            if c - keep[-1] > math.radians(2.2):
                keep.append(c)
        if 2*np.pi - keep[-1] + keep[0] < math.radians(2.2):
            keep.pop()
        return np.array(keep)

    def build_cap(self):
        rings = [0.0, 0.07, 0.16, 0.26, 0.36, 0.46, 0.56, 0.65, 0.73, 0.80, 0.86, 0.91, 0.95, 0.98, 1.0]
        cols = self.cap_columns(); nc = len(cols)
        verts = []; tvals = []; dirs = []
        pole = self.mesh_frame.A
        verts.append(self.hf.point(pole, self.r_shell(pole, 0.0))); tvals.append(0.0); dirs.append(pole)
        for t in rings[1:]:
            for ph in cols:
                d = self.mesh_frame.dir(t*float(self.th_h(ph)), ph)
                verts.append(self.hf.point(d, self.r_shell(d, t))); tvals.append(t); dirs.append(d)
        def vid(ring, col):
            return 1 + (ring-1)*nc + (col % nc)
        faces = []
        for c in range(nc):
            faces.append((0, vid(1, c), vid(1, c+1)))
        for r in range(1, len(rings)-1):
            for c in range(nc):
                faces.append((vid(r, c), vid(r+1, c), vid(r+1, c+1), vid(r, c+1)))
        verts = np.array(verts); dirs = np.array(dirs); tvals = np.array(tvals)
        self.cap_push = self.cap_clearance(verts, faces)
        # per-vertex attributes
        # hairline feather: per column, the fade starts no earlier than where skin begins under
        # the cap (t_c) and runs smoothly to the hairline (t=1). Over the open skull alpha stays 1.
        fb = self.shell.get('fade_back', 0.895)
        colphi = np.zeros(len(verts)); colphi[1:] = np.tile(cols, len(rings) - 1)
        tc_col = {}
        for ph in cols:
            ts = np.linspace(0.5, 1.0, 101)
            cov = np.array([float(self.hf.skin_cover(self.mesh_frame.dir(t*float(self.th_h(ph)), ph))) for t in ts])
            bad = np.where(cov < 0.99)[0]
            tc_col[ph] = float(ts[bad[-1]] + 0.01) if len(bad) else 0.5
        # smooth across columns (conservative: moving max, then moving average) -> no notches
        tcv = np.array([tc_col[ph] for ph in cols]); n_ = len(tcv)
        mx = np.max([np.roll(tcv, k) for k in range(-2, 3)], axis=0)
        sm = np.mean([np.roll(mx, k) for k in range(-2, 3)], axis=0)
        tc_col = {ph: float(v) for ph, v in zip(cols, np.maximum(sm, tcv))}
        azv = np.abs(fc.dir_to_azel(dirs)[0]); wb = fc.smoothstep(100, 150, azv)
        f_style = 0.895*(1 - wb) + fb*wb
        f0 = np.array([max(f_style[i], tc_col.get(colphi[i], 0.5)) if i > 0 else 1.0 for i in range(len(verts))])
        f0 = np.minimum(f0, 0.97)
        alpha = 1 - fc.smoothstep(f0, 1.0, tvals) if False else 1 - np.clip((tvals - f0)/(1.0 - f0), 0, 1)
        alpha = alpha*alpha*(3 - 2*alpha)
        cover = fc.smoothstep(0.5, 1.0, np.array([float(self.hf.skin_cover(d)) for d in dirs]))
        alpha = 1 - (1 - alpha)*cover          # never fade over (or half over) the open skull
        self.fade_start = {'min': float(f0[1:].min()), 'max': float(f0[1:].max())}
        normals = np.array([fc.surface_normal(lambda dd: self.r_shell(dd), d, eps=0.035) for d in dirs])
        thf, phf = self.flow_frame.polar(dirs)
        u = phf/(2*np.pi)*self.K; v = thf*R0/TILE
        return verts, faces, dict(alpha=alpha, normal=normals, u=u, v=v, t=tvals, cols=nc)

    def cap_clearance(self, verts, faces, margin=0.0004, iters=12):
        """Push cap faces outward until no skin vertex / sampled skin point lies within `margin`
        of (or above) the cap surface along the radial direction. Modifies verts in place."""
        from mathutils.bvhtree import BVHTree
        from mathutils import Vector
        hf = self.hf; C = hf.Cn
        tris = []
        for f in faces:
            tris += [(f[0], f[1], f[2])] if len(f) == 3 else [(f[0], f[1], f[2]), (f[0], f[2], f[3])]
        # skin probe points: all skin vertices + triangle centroids/edge midpoints
        probes = []
        for T in (hf.T_skin,):
            pass
        sk = self._skin_points()
        pushes = 0
        for it in range(iters):
            bvh = BVHTree.FromPolygons([tuple(v) for v in verts], tris, epsilon=0.0)
            need = {}
            for p in sk:
                d = p - C; r = np.linalg.norm(d); d = d/r
                loc, n, i, dist = bvh.ray_cast(Vector(C + d*0.5), Vector(-d), 0.5)
                if loc is None:
                    continue
                rc = (np.array(loc) - C) @ d
                deficit = r + margin - rc
                if deficit > 0:
                    for v in tris[i]:
                        need[v] = max(need.get(v, 0.0), deficit*1.25)
            if not need:
                break
            pushes += smooth_push(verts, need, adjacency(tris), C)
        return {'iterations': it + 1, 'vertex_pushes': pushes, 'remaining': len(need)}

    def _skin_points(self):
        """Dense skin probes: every face/back-scalp triangle sampled on a barycentric grid (n=8),
        the same sampler used by the verification probe (penetration.skin_samples)."""
        if hasattr(self.hf, '_skin_pts'):
            return self.hf._skin_pts
        import penetration as pen
        self.hf._skin_pts = pen.skin_samples([bpy.data.objects[fc.FACE_OBJ], bpy.data.objects[fc.BACK_OBJ]], n=8)
        return self.hf._skin_pts

    # ------------------------------------------------------------------ cards
    def march(self, phi_f, h_of, drift=0.0, th0=None):
        """Points along a flow meridian, from the flow pole outward (theta 0.5..178 deg)."""
        ths = np.radians(np.arange(0.5, 178, 0.35))
        ph = np.full_like(ths, phi_f)
        if drift and th0 is not None:
            ph = phi_f + drift*np.maximum(ths - th0, 0)
        D = self.flow_frame.dir(ths, ph)
        T = np.array([float(x) for x in self.t_of(D)])
        return ths, D, T

    def phi_for_hairline_az(self, targets):
        """Flow-meridian phi whose hairline crossing has the given global azimuth.
        Whorl styles: first outward exit of the cap. External flow pole: first entry into the cap.
        Meridians that never cross the cap are excluded."""
        phis = np.linspace(0, 2*np.pi, 1441)[:-1]; azs = []; ok = []
        for ph in phis:
            ths, D, T = self.march(ph, None)
            k = np.argmax(T > 1.0) if self.flow_frame is self.mesh_frame else np.argmax(T <= 1.0)
            valid = (T > 1.0).any() if self.flow_frame is self.mesh_frame else (T <= 1.0).any()
            azs.append(float(fc.dir_to_azel(D[k])[0]) if valid else np.nan); ok.append(valid)
        azs = np.array(azs); ok = np.array(ok); out = []
        for a in targets:
            diff = np.abs((azs - a + 180) % 360 - 180); diff[~ok] = np.inf
            out.append(phis[int(np.argmin(diff))])
        return out

    def card(self, phi_f, row, a_deg, k):
        mode = row.get('mode', 'outward')
        layer = (self._card_counter % 5) + row.get('layer', 0); self._card_counter += 1
        h0 = 0.0007 + 0.00045*layer
        lift = row.get('lift', 0.0)
        ths, D, T = self.march(phi_f, None)
        if mode == 'outward':
            i0 = int(np.argmax(T >= row['t_root'])); ihl = int(np.argmax(T > 1.0))
            ext = (row['ext'](a_deg) + row.get('jitter', 0.0)*math.sin(12.9898*k + 78.233*row['az'][0]))/1000
            if row.get('drift'):
                rate = math.radians(row['drift'])*math.sin(4.1*k + 1.3)/math.radians(30)
                ths, D, T = self.march(phi_f, None, drift=rate, th0=ths[i0])
        else:
            ii = np.where(T <= row['t_entry'])[0]
            if len(ii) == 0:
                return None
            i0 = int(ii[0]); ihl = None
        # build polyline with arc length
        pts = []; s_acc = 0.0; prev = None; s_hl = None; arc = []
        for i in range(i0, len(ths)):
            d = D[i]; on = T[i] <= 1.0
            if not on and s_hl is None and mode == 'outward':
                s_hl = s_acc
            s_off = 0.0 if (s_hl is None) else (s_acc - s_hl)
            h = h0 + lift*s_off
            r = self.r_surf(d) + h
            p = self.hf.point(d, r)
            if prev is not None:
                s_acc += float(np.linalg.norm(p - prev))
            az, el = fc.dir_to_azel(d)
            if abs(float(az)) < 60 and p[2] < FRINGE_ZMIN and p[1] < -0.05:
                break
            if math.isfinite(self.hf.r_ear(d)) and (s_hl is not None or mode != 'outward'):
                break       # cards end at the (FACE52, un-pinned) ear rim instead of cutting through it
            if mode == 'outward' and s_hl is not None and on:
                break       # card left the cap and would cut back into it (temple corner): end here
            pts.append(p); arc.append(s_acc); prev = p
            if mode == 'outward' and s_hl is not None and s_acc - s_hl >= ext:
                break
            if mode != 'outward' and s_acc >= row['length'](a_deg)/1000:
                break
        pts = np.array(pts); arc = np.array(arc)
        if len(pts) < 3:
            return None
        n = row['segs']; L = arc[-1]
        ss = np.linspace(0, L, n+1)
        C = np.array([np.interp(ss, arc, pts[:, j]) for j in range(3)]).T
        rows_v = []; rows_n = []
        w = row['w']/1000*(1 + row.get('wvar', 0.0)*math.sin(7.31*k + 2.1))
        for i in range(n+1):
            tgt = C[min(i+1, n)] - C[max(i-1, 0)]; tgt /= np.linalg.norm(tgt)
            d = (C[i] - self.hf.Cn); d /= np.linalg.norm(d)
            nrm = fc.surface_normal(self.r_surf, d, eps=0.035)
            lat = np.cross(nrm, tgt); lat /= np.linalg.norm(lat)
            wi = w*(1 - 0.30*ss[i]/max(L, 1e-6))
            hi = (C[i] - self.hf.Cn) @ d - self.r_surf(d)      # current height above surface
            pair = []
            for sgn in (-1, 1):
                q = C[i] + sgn*lat*wi/2
                dq = (q - self.hf.Cn); rq = np.linalg.norm(dq); dq /= rq
                rmin = self.r_surf(dq) + max(hi, h0)
                pair.append(self.hf.point(dq, max(rq, rmin)))
            rows_v.append(pair); rows_n.append(nrm)
        strip = row['strips'][k % len(row['strips'])]
        return dict(v=np.array(rows_v), n=np.array(rows_n), strip=strip, length=L, name=row['name'], layer=layer)

    def build_cards(self):
        cards = []; self._card_counter = 0
        for row in self.s['cards']:
            a0, a1 = row['az']; azs = list(np.linspace(a0, a1, row['n']))
            if row.get('mirror'):
                azs = azs + [-a for a in azs]
            phis = self.phi_for_hairline_az(azs)
            for k, (a, ph) in enumerate(zip(azs, phis)):
                c = self.card(ph, row, a, k)
                if c is not None:
                    cards.append(c)
        return cards


def _push_out(V, idx, amount, C):
    for v in idx:
        d = V[v] - C; V[v] = V[v] + d/np.linalg.norm(d)*amount


def adjacency(tris):
    adj = {}
    for t in tris:
        for a in t:
            adj.setdefault(a, set()).update(t)
    return adj


def smooth_push(V, need, adj, C, weights=(1.0, 0.6, 0.3)):
    """Apply radial pushes {vertex: amount} spread over 1- and 2-ring neighbours (max-combined),
    so clearance fixes do not leave spikes in the surface."""
    total = {}
    for v, amt in need.items():
        ring = {v}; seen = {v}
        for w in weights:
            for u in ring:
                total[u] = max(total.get(u, 0.0), amt*w)
            nxt = set()
            for u in ring:
                nxt |= adj.get(u, set())
            ring = nxt - seen; seen |= ring
    for v, amt in total.items():
        d = V[v] - C; V[v] = V[v] + d/np.linalg.norm(d)*amt
    return len(total)


def overlap_pass(V, tris, obstacles, C, step=0.0003, iters=40, self_layers=None, smooth=False):
    """Push movable triangles (radially outward) until they no longer overlap the obstacle
    triangle sets (BVH triangle-triangle overlap, epsilon 0). With self_layers, overlapping
    movable pairs that share no vertex are resolved by pushing the higher-layer triangle."""
    from mathutils.bvhtree import BVHTree
    pushed = 0; remaining = 0
    for it in range(iters):
        bm = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in tris], all_triangles=True, epsilon=0.0)
        hit = set()
        for OV, OT in obstacles:
            bo = BVHTree.FromPolygons([tuple(v) for v in OV], [tuple(t) for t in OT], all_triangles=True, epsilon=0.0)
            hit.update(i for i, j in bm.overlap(bo))
        if self_layers is not None:
            for i, j in bm.overlap(bm):
                if i < j and not (set(tris[i]) & set(tris[j])):
                    hit.add(i if self_layers[i] >= self_layers[j] else j)
        remaining = len(hit)
        if not hit:
            break
        idx = {v for t in hit for v in tris[t]}
        if smooth:
            pushed += smooth_push(V, {v: step for v in idx}, adjacency(tris), C)
        else:
            _push_out(V, idx, step, C); pushed += len(idx)
    return {'iterations': it + 1, 'vertex_pushes': pushed, 'remaining_overlapping_triangles': remaining}


def build_object(hf, sid, spec, cap_img, card_img):
    hb = HairBuilder(hf, sid, spec)
    C = hf.Cn
    cv, cf, ca = hb.build_cap()
    # skin triangle set (face + back scalp) for overlap passes
    sk_v = []; sk_t = []; off = 0
    for name in (fc.FACE_OBJ, fc.BACK_OBJ):
        m = bpy.data.objects[name].data; co = np.array([v.co[:] for v in m.vertices]); sk_v.append(co)
        for p_ in m.polygons:
            vs = list(p_.vertices); sk_t += [(vs[0]+off, vs[k]+off, vs[k+1]+off) for k in range(1, len(vs)-1)]
        off += len(co)
    SKV = np.concatenate(sk_v); SKT = sk_t
    # ---- cap: explicit triangles (deterministic triangulation) with per-corner UVs
    V = np.array(cv, float); tris = []; tri_mat = []; uv = []; col = []; nrm = []
    for f in cf:
        us = [ca['u'][i] for i in f]
        if len(f) == 3 and f[0] == 0:            # pole fan: pole u = mid of its two neighbours
            uu = us[1:]; uu = [uu[0], uu[1] + (hb.K if uu[1] < uu[0] - hb.K/2 else 0)]
            us = [(uu[0]+uu[1])/2] + uu
        else:
            base = us[0]
            us = [x + hb.K if x < base - hb.K/2 else (x - hb.K if x > base + hb.K/2 else x) for x in us]
        corner = [((u, ca['v'][i]), (1, 1, 1, ca['alpha'][i]), ca['normal'][i]) for i, u in zip(f, us)]
        for tri in ([(0, 1, 2)] if len(f) == 3 else [(0, 1, 2), (0, 2, 3)]):
            tris.append(tuple(f[j] for j in tri)); tri_mat.append(0)
            for j in tri:
                uv.append(corner[j][0]); col.append(corner[j][1]); nrm.append(corner[j][2])
    ncap_tris = len(tris)
    cap_overlap = overlap_pass(V, tris, [(SKV, SKT)], C, smooth=True)
    # cards follow the actual (pushed) cap surface from here on
    hb.set_cap_mesh(V, tris)
    cards = hb.build_cards()
    layers = []
    for c in cards:
        nrow = c['v'].shape[0]; base = len(V)
        V = np.vstack([V, c['v'].reshape(-1, 3)])
        u0, u1 = c['strip']/4 + 0.006, (c['strip']+1)/4 - 0.006
        for i in range(nrow-1):
            a, b = base + 2*i, base + 2*i + 1; cc, dd = base + 2*(i+1) + 1, base + 2*(i+1)
            va, vb = 1 - i/(nrow-1), 1 - (i+1)/(nrow-1)
            q = [(a, (u0, va), i), (b, (u1, va), i), (cc, (u1, vb), i+1), (dd, (u0, vb), i+1)]
            for tri in ((0, 1, 2), (0, 2, 3)):
                tris.append(tuple(q[j][0] for j in tri)); tri_mat.append(1); layers.append(c['layer'])
                for j in tri:
                    uv.append(q[j][1]); col.append((1, 1, 1, 1)); nrm.append(c['n'][q[j][2]])
    card_tris = tris[ncap_tris:]
    CV = V  # shared array; card passes move only card vertices
    cap_obst = (V[:len(cv)].copy(), tris[:ncap_tris])
    sub = np.unique(np.array(card_tris).ravel()) if card_tris else np.array([], int)
    if len(card_tris):
        remap = {int(v): k for k, v in enumerate(sub)}
        LV = V[sub].copy(); LT = [tuple(remap[v] for v in t) for t in card_tris]; L0 = LV.copy()
        card_overlap = overlap_pass(LV, LT, [(SKV, SKT), cap_obst], C, iters=40)
        mv = np.linalg.norm(LV - L0, axis=1)
        card_overlap['card_vertex_push_mm'] = {'max': round(float(mv.max())*1000, 3), 'p95': round(float(np.percentile(mv, 95))*1000, 3), 'moved_vertices': int((mv > 0).sum()), 'total_vertices': int(len(mv))}
        V[sub] = LV
    else:
        card_overlap = None
    # orient every triangle so its geometric normal agrees with its custom (surface) normals;
    # Cycles flips the shading normal on back-face hits, so a mismatch renders inside-lit/dark.
    flipped = 0; uv2 = []; col2 = []; nrm2 = []; tris2 = []
    for k, t in enumerate(tris):
        P = V[list(t)]; gn = np.cross(P[1] - P[0], P[2] - P[0]); nn = np.mean(nrm[3*k:3*k+3], axis=0)
        order = (0, 2, 1) if gn @ nn < 0 else (0, 1, 2)
        flipped += order != (0, 1, 2)
        tris2.append(tuple(t[j] for j in order))
        for j in order:
            uv2.append(uv[3*k+j]); col2.append(col[3*k+j]); nrm2.append(nrm[3*k+j])
    ob = fc.new_mesh_object('REF09_Hair', V, tris2)
    me = ob.data; me.name = f'TMH53_{spec["label"]}'
    me.polygons.foreach_set('material_index', tri_mat)
    fc.set_loop_attrs(me, uv_per_loop=uv2, col_per_loop=col2, normal_per_loop=nrm2)
    for p_ in me.polygons:
        p_.use_smooth = True
    extras = {'fh53_status': 'RESEARCH CANDIDATE - not approved, not production', 'fh53_hair_id': spec['label'],
              'provenance': 'Procedural strand texture generated by make_hair_textures.py (no source pixels).'}
    ob.data.materials.append(fc.make_textured_material(f'TMH53_{sid}_Cap', cap_img, 'BLEND', extras=extras))
    ob.data.materials.append(fc.make_textured_material(f'TMH53_{sid}_Cards', card_img, 'BLEND', extras=extras))
    info = {'hair_id': spec['label'], 'intent_ja': spec['intent_ja'], 'cap_vertices': len(cv), 'cap_triangles': ncap_tris,
            'cap_columns': ca['cols'], 'cards': len(cards), 'card_triangles': len(card_tris),
            'card_rows': {r['name']: sum(1 for c in cards if c['name'] == r['name']) for r in spec['cards']},
            'mesh_pole_azel': spec['pole'], 'flow_pole_azel': spec.get('flow', {}).get('pole', spec['pole']),
            'hairline_azel_controls': spec.get('asym_line') or mirror_line(spec['line']),
            'shell': {k: v for k, v in spec['shell'].items()}, 'triangles_rewound_to_match_normals': int(flipped),
            'cap_radial_clearance_pass': hb.cap_push, 'cap_vs_skin_overlap_pass': cap_overlap,
            'card_vs_skin_cap_and_layer_overlap_pass': card_overlap, 'alpha_fade_start_t': hb.fade_start}
    return ob, hb, info


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only', default='H1,H2,H3,H4'); ap.add_argument('--preview', action='store_true')
    ap.add_argument('--out', default=str(fc.BUILD))
    a = ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    out = Path(a.out); inputs = fc.check_inputs()
    tex = out/'textures'
    log = {'blender': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash,
           'inputs': inputs, 'textures': {p.name: fc.sha256(p) for p in sorted(tex.glob('TMH53_*.png'))}, 'hairs': {}}
    for sid in a.only.split(','):
        t0 = time.time()
        bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))      # read-only use
        face = bpy.data.objects[fc.FACE_OBJ]; back = bpy.data.objects[fc.BACK_OBJ]; old = bpy.data.objects[fc.HAIR_OBJ]
        hf = fc.HeadField(face, back, old)
        # new file containing only the new hair (+ reference copies are NOT kept)
        old.name = 'FACE52_H0_reference_unused'
        cap_img = fc.load_packed_image(tex/'TMH53_CAP_STRANDS_512.png', 'TMH53_CAP_STRANDS_512')
        card_img = fc.load_packed_image(tex/'TMH53_CARD_STRANDS_512.png', 'TMH53_CARD_STRANDS_512')
        ob, hb, info = build_object(hf, sid, STYLES[sid], cap_img, card_img)
        # keep only the hair object in the saved hair file
        for o in list(bpy.data.objects):
            if o is not ob:
                bpy.data.objects.remove(o, do_unlink=True)
        for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
            for blk in list(coll):
                if blk.users == 0:
                    coll.remove(blk)
        sc = bpy.context.scene
        for k in list(sc.keys()):
            if k != 'cycles':
                del sc[k]
        sc['fh53_role'] = 'HAIR candidate module (replaces REF09_Hair). Head-local FACE52 frame, identity transform.'
        sc['fh53_status'] = 'RESEARCH CANDIDATE. Not approved, not production, no rights clearance.'
        sc['fh53_hair_id'] = STYLES[sid]['label']
        name = f'TM_FH53_{STYLES[sid]["label"]}'
        blend = out/'models/hair'/(name + '.blend'); glb = blend.with_suffix('.glb')
        fc.save_blend(blend); fc.export_glb(glb)
        info.update({'blend': blend.name, 'glb': glb.name, 'blend_sha256': fc.sha256(blend), 'glb_sha256': fc.sha256(glb),
                     'export': 'plain Blender glTF export (no canonical_cap: new scalp shape)', 'seconds': round(time.time()-t0, 1)})
        log['hairs'][sid] = info
        print('BUILT', sid, {k: info[k] for k in ('cap_triangles', 'card_triangles', 'cap_vs_skin_overlap_pass', 'card_vs_skin_cap_and_layer_overlap_pass', 'seconds')}, flush=True)
    fc.write_json(out/'qa'/f'build_hairs_{"_".join(a.only.split(","))}.json', log)


if __name__ == '__main__':
    main()
    fc.finish()
