"""FH54 per-face skin textures, derived procedurally from FACE52's face/side/neck/eye textures.

Inputs : FACE52 packed images (face_F2 1024, TM11_Face512, skincomm__x00skn 128, eyeballtex 64), read from
         the FACE52 native .blend (read-only).
Outputs: build/textures/faces/TMF54_<F>_{FACE,SIDE,NECK,EYE}.png for F1..F3 + params JSON.
Edits (UV pixel space of the frontal face texture; right side = image left, mirrored for the left side):
  * skin tone transform (same transform on FACE/SIDE/NECK so the face, jaw-side pieces and back scalp match)
  * back-scalp/side harmonisation: SIDE and NECK textures are scaled so that their texture x vertex-colour mean
    equals the face skin mean (removes the V-shaped tone seam seen under short hair)
  * eyebrows: original brow hair removed (dark-pixel mask + harmonic fill + skin grain), new brows drawn as strands
  * eye area (crease / lash line / under-eye), lips tint, cheek blush or contour, stubble, mole, iris tint
Still a DERIVED research texture (FACE52 base pixels remain). Deterministic (fixed seeds).
Usage: python face_textures54.py
"""
import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import binary_dilation, gaussian_filter
import fh53_common as fc

# ---------------------------------------------------------------- per-face design parameters
FACES = {
    'F1': dict(label='F1_LONG_ANGULAR',
               tone=(0.92, 0.86, 0.80), lift=0.0,                       # warmer, tanned
               brow=dict(x_in=372, x_out=92, y_in=414, y_peak=404, x_peak=200, y_out=414, th_in=30, th_mid=26, th_out=14,
                         color=(26, 19, 16), density=1.3, angle_in=-55, angle_out=-12),
               crease=None, lash=dict(strength=0.22, width=3), under_eye=0.10,
               lips=dict(sat=0.75, dark=0.95), blush=None, contour=dict(strength=0.10), stubble=dict(strength=0.16),
               nose_shade=0.10, mole=None, iris=(0.80, 0.70, 0.62)),
    'F2': dict(label='F2_ROUND_SOFT',
               tone=(1.00, 0.97, 0.97), lift=0.035,                      # fairer, rosy
               brow=dict(x_in=366, x_out=118, y_in=416, y_peak=388, x_peak=228, y_out=406, th_in=20, th_mid=17, th_out=9,
                         color=(50, 35, 27), density=1.0, angle_in=-60, angle_out=-20),
               crease=dict(offset=13, strength=0.20), lash=dict(strength=0.14, width=2), under_eye=0.0,
               lips=dict(sat=1.25, dark=1.0, pink=0.06), blush=dict(strength=0.10), contour=None, stubble=None,
               nose_shade=0.0, mole=None, iris=(1.05, 0.95, 0.80)),
    'F3': dict(label='F3_NARROW_SHARP',
               tone=(0.97, 0.94, 0.94), lift=0.0,                        # neutral, slightly cooler
               brow=dict(x_in=360, x_out=110, y_in=420, y_peak=384, x_peak=178, y_out=412, th_in=23, th_mid=19, th_out=7,
                         color=(32, 23, 20), density=1.15, angle_in=-40, angle_out=-35),
               crease=None, lash=dict(strength=0.32, width=3), under_eye=0.04,
               lips=dict(sat=0.95, dark=0.97, pink=0.02), blush=None, contour=dict(strength=0.16, high=True), stubble=None,
               nose_shade=0.06, mole=dict(x=716, y=566, r=3.2), iris=(1.10, 1.00, 0.78)),
}
# FACE52 face_F2 landmark regions (pixel coords, 1024 image, right side = image left)
BROW_BAND = (60, 360, 470, 448)           # x0,y0,x1,y1 for the right brow (mirrored for left)
EYE = dict(inner=(367, 484), apex=(265, 466), outer=(160, 480))
LIPS = (318, 782, 706, 868)
FOREHEAD_PATCH = (420, 150, 604, 300)


def mirror_x(x):
    return 1023 - x


def lum(a):
    return a[..., 0]*0.299 + a[..., 1]*0.587 + a[..., 2]*0.114


def remove_brows(img):
    """Remove the original brow hair by normalized convolution: the skin under the brow is estimated from the
    surrounding non-hair skin pixels (keeps the local shading gradient), then skin grain is restored."""
    a = img.copy(); H, W, _ = a.shape
    hair = np.zeros((H, W), bool)
    x0, y0, x1, y1 = BROW_BAND
    for flip in (False, True):
        xa, xb = (mirror_x(x1), mirror_x(x0)) if flip else (x0, x1)
        reg = a[y0:y1, xa:xb]; L = lum(reg)
        from scipy.ndimage import median_filter
        local = median_filter(L, 21)
        hair[y0:y1, xa:xb] |= (L < 135) | (L < local - 22)
    hair = binary_dilation(hair, iterations=3)
    keep = (~hair).astype(float)
    est = np.zeros_like(a); est_ok = np.zeros((H, W), bool)
    for sig in (6, 10, 16, 26):          # widen until every hair pixel has nearby skin support
        num = gaussian_filter(a*keep[..., None], (sig, sig, 0)); den = gaussian_filter(keep, sig)
        e = num/np.maximum(den, 1e-6)[..., None]
        new_ok = (den > 0.15) & ~est_ok
        est[new_ok] = e[new_ok]; est_ok |= new_ok
    est[~est_ok] = e[~est_ok]                 # widest estimate wherever support stayed low
    remove_brows.stats = {'hair_pixels': int(hair.sum()), 'unsupported_after_26px': int((~est_ok & hair).sum())}
    px0, py0, px1, py1 = FOREHEAD_PATCH; patch = img[py0:py1, px0:px1]
    hp = patch - gaussian_filter(patch, (6, 6, 0))
    grain = np.tile(hp, (int(np.ceil(H/hp.shape[0])), int(np.ceil(W/hp.shape[1])), 1))[:H, :W]
    fx0, fy0, fx1, fy1 = FOREHEAD_PATCH; ref = img[fy0:fy1, fx0:fx1].reshape(-1, 3).mean(0)
    est = est + 0.30*(ref - est)*fc.smoothstep(0, 1, gaussian_filter(hair.astype(float), 4.0))[..., None]   # lift the brow ghost
    soft = np.clip(gaussian_filter(hair.astype(float), 2.5)*1.3, 0, 1)[..., None]
    out = img*(1 - soft) + (est + grain*0.9)*soft
    return np.clip(out, 0, 255), hair


def brow_layer(size, p, seed):
    """Strand-drawn eyebrow for the right side (image left) at 4x supersampling; returns RGBA float (H,W,4)."""
    S = 4; W = H = size*S
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    rng = np.random.default_rng(seed)
    xs = np.linspace(p['x_in'], p['x_out'], 220)
    def yc(x):        # quadratic through inner, peak, outer
        X = np.array([p['x_in'], p['x_peak'], p['x_out']]); Y = np.array([p['y_in'], p['y_peak'], p['y_out']])
        return np.polyval(np.polyfit(X, Y, 2), x)
    def th(t):
        return np.interp(t, [0, 0.45, 1], [p['th_in'], p['th_mid'], p['th_out']])
    # soft 'mass' under the strands (brow body), then strands on top
    poly_top = [(x*S, (yc(x) - th((x - p['x_in'])/(p['x_out'] - p['x_in']))/2)*S) for x in xs]
    poly_bot = [(x*S, (yc(x) + th((x - p['x_in'])/(p['x_out'] - p['x_in']))/2)*S) for x in xs[::-1]]
    mass = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(mass).polygon(poly_top + poly_bot, fill=tuple(p['color']) + (int(95*p['density']),))
    mass = mass.filter(ImageFilter.GaussianBlur(S*2.2)); lay = Image.alpha_composite(lay, mass); dr = ImageDraw.Draw(lay)
    n = int(2100*p['density'])
    for _ in range(n):
        t = rng.random()**0.9; x = p['x_in'] + (p['x_out'] - p['x_in'])*t
        half = th(t)/2; y = yc(x) + rng.uniform(-half, half)
        ang = math.radians(np.interp(t, [0, 0.25, 1], [p['angle_in'], (p['angle_in'] + p['angle_out'])/2, p['angle_out']]) + rng.normal(0, 7))
        L = rng.uniform(9, 17)*(1 - 0.35*t)
        dx = -math.cos(ang)*L; dy = math.sin(ang)*L        # strands grow toward the tail (image left) and upward
        a = int(np.clip(rng.normal(175, 35)*(0.7 + 0.3*(1 - abs(y - yc(x))/max(half, 1))), 40, 240))
        c = tuple(int(np.clip(v + rng.normal(0, 6), 0, 255)) for v in p['color'])
        dr.line([(x*S, y*S), ((x + dx)*S, (y + dy)*S)], fill=c + (a,), width=int(rng.uniform(1.2, 2.2)*S/1.6))
    lay = lay.filter(ImageFilter.GaussianBlur(S*0.45)).resize((size, size), Image.LANCZOS)
    return np.asarray(lay).astype(float)


def over(base, rgba):
    a = rgba[..., 3:4]/255.0
    return base*(1 - a) + rgba[..., :3]*a


def mirror_layer(rgba):
    return rgba[:, ::-1]


def gauss_mask(H, W, cx, cy, sx, sy, rot=0.0):
    y, x = np.mgrid[0:H, 0:W].astype(float); x -= cx; y -= cy
    c, s = math.cos(rot), math.sin(rot); xr = c*x + s*y; yr = -s*x + c*y
    return np.exp(-0.5*((xr/sx)**2 + (yr/sy)**2))


def lid_curve(offset=0.0, n=120):
    (xi, yi), (xa, ya), (xo, yo) = EYE['inner'], EYE['apex'], EYE['outer']
    X = np.array([xi, xa, xo]); Y = np.array([yi, ya, yo]); co = np.polyfit(X, Y, 2)
    xs = np.linspace(xo, xi, n); return xs, np.polyval(co, xs) - offset


def stroke_mask(H, W, xs, ys, width, taper=True):
    m = Image.new('L', (W*2, H*2), 0); d = ImageDraw.Draw(m)
    for i in range(len(xs) - 1):
        t = i/(len(xs) - 1); w = width*(math.sin(math.pi*t)**0.6 if taper else 1)
        d.line([(xs[i]*2, ys[i]*2), (xs[i+1]*2, ys[i+1]*2)], fill=255, width=max(1, int(w*2)))
    m = m.filter(ImageFilter.GaussianBlur(1.6)).resize((W, H), Image.LANCZOS)
    return np.asarray(m).astype(float)/255.0


def both_sides(fn, H, W):
    m = fn(); return np.maximum(m, m[:, ::-1])


def make_face(face, src, fid):
    p = FACES[fid]; H, W, _ = src.shape
    rng = np.random.default_rng({'F1': 541, 'F2': 542, 'F3': 543}[fid])
    a, browmask = remove_brows(src)
    tone = np.array(p['tone'])
    a = a*tone + p['lift']*(255 - a*tone)
    # cheeks: blush / contour
    if p['blush']:
        m = both_sides(lambda: gauss_mask(H, W, 225, 640, 70, 45), H, W)*p['blush']['strength']
        a = a*(1 - m[..., None]) + (a*np.array([1.06, 0.90, 0.92]))*m[..., None]
    if p['contour']:
        cy = 640 if p['contour'].get('high') else 680
        m = both_sides(lambda: gauss_mask(H, W, 175, cy, 95, 28, rot=math.radians(-28)), H, W)*p['contour']['strength']
        a = a*(1 - m[..., None]*np.array([0.30, 0.42, 0.48]))      # warm brown shade, not grey
    if p['nose_shade']:
        m = (gauss_mask(H, W, 452, 580, 14, 90) + gauss_mask(H, W, 572, 580, 14, 90))*p['nose_shade']
        a = a*(1 - m[..., None])
    # stubble: speckle under a soft beard mask (jaw, chin, upper lip), excluding lips
    if p['stubble']:
        beard = (gauss_mask(H, W, 512, 930, 300, 110) + both_sides(lambda: gauss_mask(H, W, 140, 820, 70, 150), H, W)*0.8
                 + gauss_mask(H, W, 512, 765, 120, 22)*0.9)
        lipmask = gauss_mask(H, W, 512, 825, 170, 32)
        beard = np.clip(beard - 1.4*lipmask, 0, 1)
        beard *= (gauss_mask(H, W, 512, 1100, 600, 330) > 0.05)
        speck = (rng.random((H, W)) < 0.20).astype(float); speck = gaussian_filter(speck, 0.7)
        s = np.clip(beard*(0.55 + 1.4*speck), 0, 1.3)*p['stubble']['strength']
        a = a*(1 - s[..., None]*np.array([0.62, 0.60, 0.52]))
    # eyes: crease, lash line, under-eye
    if p['crease']:
        xs, ys = lid_curve(p['crease']['offset'])
        m = both_sides(lambda: stroke_mask(H, W, xs, ys, 3.0), H, W)*p['crease']['strength']
        a = a*(1 - m[..., None]*np.array([0.55, 0.62, 0.62]))
    if p['lash']:
        xs, ys = lid_curve(-1.0)
        m = both_sides(lambda: stroke_mask(H, W, xs, ys, p['lash']['width'], taper=False), H, W)*p['lash']['strength']
        a = a*(1 - m[..., None])
    if p['under_eye']:
        m = both_sides(lambda: gauss_mask(H, W, 262, 512, 75, 10), H, W)*p['under_eye']
        a = a*(1 - m[..., None]*np.array([0.5, 0.6, 0.5]))
    # lips: saturation / darkness / pink within a soft lip mask
    lm = gauss_mask(H, W, 512, 825, 175, 34)**1.5
    g = lum(a)[..., None]
    lipc = (g + (a - g)*p['lips']['sat'])*p['lips']['dark']
    if p['lips'].get('pink'):
        lipc = lipc*(1 + np.array([p['lips']['pink'], -p['lips']['pink']*0.6, -p['lips']['pink']*0.2]))
    a = a*(1 - lm[..., None]) + lipc*lm[..., None]
    # brows (new), drawn on top of the cleaned skin
    br = brow_layer(W, p['brow'], {'F1': 11, 'F2': 12, 'F3': 13}[fid])
    a = over(a, br); a = over(a, mirror_layer(br))
    if p['mole']:
        m = gauss_mask(H, W, p['mole']['x'], p['mole']['y'], p['mole']['r'], p['mole']['r'])
        a = a*(1 - 0.55*m[..., None]) + np.array([92, 62, 50])*0.55*m[..., None]
    return np.clip(a, 0, 255), browmask


def seam_means(bpy, tex):
    """texture x vertex-colour sRGB means per object/material on FACE52 (corner samples)."""
    out = {}
    for obn in (fc.FACE_OBJ, fc.BACK_OBJ):
        ob = bpy.data.objects[obn]; me = ob.data; names = [s_.material.name for s_ in ob.material_slots]
        uv = [d.uv[:] for d in me.uv_layers[0].data]; col = me.color_attributes['Col']
        acc = {}
        for p_ in me.polygons:
            m = names[p_.material_index]
            if m not in tex:
                continue
            T = tex[m]; h, w, _ = T.shape
            for l in p_.loop_indices:
                u, v = uv[l]; px = T[int(np.clip((1 - v % 1)*h, 0, h - 1)), int(np.clip((u % 1)*w, 0, w - 1))]
                acc.setdefault(m, []).append(px*np.array(col.data[l].color_srgb[:3]))
        for m, v in acc.items():
            out[f'{obn}/{m}'] = np.array(v).mean(0).round(2).tolist()
    return out


def scale_to(img, ratio):
    return np.clip(img*np.asarray(ratio), 0, 255)


def main():
    import bpy
    fc.check_inputs()
    out = fc.BUILD/'textures/faces'; out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(fc.FACE52_BLEND))
    import io
    def img(name):
        im = Image.open(io.BytesIO(bpy.data.images[name].packed_file.data)).convert('RGBA')   # exact packed PNG bytes
        a = np.asarray(im).astype(float); return a[..., :3], a[..., 3:4]
    src = {k: img(n) for k, n in (('FACE', 'face_F2'), ('SIDE', 'TM11_Face512'), ('NECK', 'skincomm__x00skn'), ('EYE', 'eyeballtex__xm00me.bin'))}
    means = seam_means(bpy, {'TM26_Face_Skin_Only': src['FACE'][0], 'SOURCE_APPEARANCE04_slot_14': src['SIDE'][0], 'SOURCE_APPEARANCE04_slot_02': src['NECK'][0]})
    fc.write_json(fc.BUILD/'qa/skin_seam_measure.json', means)
    rec = {'inputs': fc.check_inputs(), 'faces': {}}
    for fid, p in FACES.items():
        face, browmask = make_face(p, src['FACE'][0], fid)
        tone = np.array(p['tone'])
        # back scalp: NECK(slot_02) matched to the adjacent back-scalp slot_14 region (the V-seam pair);
        # SIDE keeps its own shading (ratio 1) and only receives the face tone.
        side_ratio = np.ones(3)
        neck_ratio = np.array(means['REF14_BackScalp/SOURCE_APPEARANCE04_slot_14'])/np.array(means['REF14_BackScalp/SOURCE_APPEARANCE04_slot_02'])
        side = src['SIDE'][0]*side_ratio*tone; side = side + p['lift']*(255 - side)
        neck = src['NECK'][0]*neck_ratio*tone; neck = neck + p['lift']*(255 - neck)
        eye = src['EYE'][0].copy(); E = eye.shape[0]
        y, x = np.mgrid[0:E, 0:E]; r = np.hypot(x - E/2 + 0.5, y - E/2 + 0.5)
        irism = (r < E*0.22).astype(float)[..., None]
        eye = eye*(1 - irism) + eye*np.array(p['iris'])*irism
        files = {}
        for key, arr, alpha in (('FACE', face, src['FACE'][1]), ('SIDE', side, src['SIDE'][1]), ('NECK', neck, src['NECK'][1]), ('EYE', eye, src['EYE'][1])):
            rgba = np.concatenate([np.clip(arr, 0, 255), alpha], -1).astype(np.uint8)
            f = out/f'TMF54_{fid}_{key}.png'; Image.fromarray(rgba, 'RGBA').save(f); files[key] = {'png': f.name, 'sha256': fc.sha256(f)}
        rec['faces'][fid] = {'label': p['label'], 'params': {k: v for k, v in p.items() if k != 'label'}, 'side_ratio': side_ratio.round(4).tolist(),
                             'neck_ratio': neck_ratio.round(4).tolist(), 'brow_pixels_removed': int(browmask.sum()), 'files': files}
        print('TEXTURES', fid, files['FACE']['png'], flush=True)
    fc.write_json(fc.BUILD/'qa/face_textures54.json', rec)


if __name__ == '__main__':
    main()
    fc.finish()
