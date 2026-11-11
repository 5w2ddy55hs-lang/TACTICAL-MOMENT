"""HM55 procedural hair textures (strand patterns synthesised with numpy, fixed seeds; no image is read).
Same generator as the FH53/FH54 hair textures (own code); tone = authored near-black with thin lighter streaks.

Outputs (PNG, RGBA, straight alpha):
  TMH55_CAP_STRANDS_512.png      tileable in U and V, alpha = 1. Strands run along V.
  TMH55_CARD_STRANDS_512.png     vertical strips; top of image = root (UV v = 1), bottom = tips. Alpha fades in
                                 over the root band and tapers into separate locks toward the tip.
  TMH55_EDGE_STRANDS_512x256.png hairline band: strands end at random heights so the edge breaks into tips.

Usage: python hm_hair_textures.py OUTPUT_DIR
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

SIZE = 512
BASE = 0.060


def fc_root_fade(ys):
    """FH54: smooth root fade over the first 22% of the strip (FH53: linear over 10%), so card roots blend into the cap."""
    t = np.clip(ys/0.22, 0, 1)
    return t*t*(3 - 2*t)          # sRGB base value between strands (FACE52 hair texel mean ~0.08-0.095)


def _strand_layer(rng, h, w, count, length_range, bright_mu, bright_sd, wave_amp, wrap=True, sig_range=(0.45, 0.9)):
    """Accumulate anti-aliased vertical strands. Returns (value, coverage)."""
    val = np.zeros((h, w)); cov = np.zeros((h, w))
    ys = np.arange(h)
    for _ in range(count):
        x0 = rng.uniform(0, w); y0 = rng.uniform(0, h)
        L = rng.uniform(*length_range)
        b = max(0.0, rng.normal(bright_mu, bright_sd))
        sig = rng.uniform(*sig_range)
        amp = rng.uniform(0, wave_amp); lam = rng.uniform(150, 420); ph = rng.uniform(0, 2*np.pi)
        t = (ys - y0) % h if wrap else ys - y0
        on = (t >= 0) & (t < L)
        if not on.any():
            continue
        rows = ys[on]; tt = t[on]
        xc = x0 + amp*np.sin(2*np.pi*tt/lam + ph)
        # fade the two ends of every strand
        endfade = np.clip(np.minimum(tt, L - tt) / 25.0, 0, 1)
        for dx in range(-2, 3):
            xi = np.floor(xc).astype(int) + dx
            dist = xi + 0.5 - xc
            wgt = np.exp(-0.5*(dist/sig)**2) * endfade
            xi = xi % w if wrap else np.clip(xi, 0, w-1)
            np.add.at(val, (rows, xi), wgt*b)
            np.add.at(cov, (rows, xi), wgt)
    return val, cov


def _lowfreq(rng, n, period, amp):
    x = np.arange(n)
    out = np.zeros(n)
    for k in range(1, 5):
        out += rng.normal(0, 1)/k*np.sin(2*np.pi*k*x/period + rng.uniform(0, 2*np.pi))
    return 1 + amp*out/np.abs(out).max()


def make_cap(out):
    rng = np.random.default_rng(5301)
    # many faint fine strands + fewer brighter highlight strands, added onto a dark base
    val, _ = _strand_layer(rng, SIZE, SIZE, 2100, (40, 260), 0.020, 0.012, 2.5, wrap=True, sig_range=(0.35, 0.6))
    val2, _ = _strand_layer(rng, SIZE, SIZE, 320, (30, 160), 0.085, 0.030, 1.5, wrap=True, sig_range=(0.35, 0.55))
    clump = _lowfreq(rng, SIZE, SIZE, 0.15)[None, :]          # tileable horizontal clumping
    v = np.clip(BASE + (val + val2)*clump, 0, 1)
    rgb = np.stack([v*1.00, v*0.97, v*0.95], -1)              # very slightly warm black
    img = np.concatenate([rgb, np.ones((SIZE, SIZE, 1))], -1)
    Image.fromarray((img*255 + 0.5).astype(np.uint8), 'RGBA').save(out)
    return {'mean_rgb': rgb.reshape(-1, 3).mean(0).round(4).tolist()}


# FH54 card atlas: five strips with explicit pixel ranges (u0,u1 in [0,1] = x/512)
STRIPS = [(0, 128), (128, 256), (256, 384), (384, 448), (448, 512)]


def make_cards(out):
    """Strips: 0 standard locks, 1 fine/thin tips, 2 chunky locks, 3 short spiky (64 px), 4 sparse hairline wisps (64 px)."""
    rng = np.random.default_rng(5302)
    H = SIZE
    rgba = np.zeros((H, SIZE, 4))
    params = [  # locks, strands per lock, min/max tip fraction, lock spread
        dict(locks=7, per=70, tip=(0.70, 0.98), spread=0.55, taper=0.22),
        dict(locks=10, per=45, tip=(0.60, 0.98), spread=0.40, taper=0.30),
        dict(locks=5, per=110, tip=(0.80, 0.97), spread=0.70, taper=0.15),
        dict(locks=5, per=40, tip=(0.45, 0.80), spread=0.45, taper=0.25),
        dict(locks=7, per=6, tip=(0.55, 0.95), spread=0.9, taper=0.45, wisp=True),
    ]
    ys = np.arange(H) / (H - 1)          # 0 = root row (top), 1 = bottom
    for s, p in enumerate(params):
        x0, x1 = STRIPS[s]; W = x1 - x0
        acc = np.zeros((H, W)); cov = np.zeros((H, W))
        centres = (np.arange(p['locks']) + 0.5 + rng.uniform(-0.25, 0.25, p['locks'])) / p['locks'] * W
        lockw = W / p['locks'] * p['spread'] * 1.8
        for c in centres:
            tipf = rng.uniform(*p['tip'])
            for _ in range(p['per']):
                off = rng.normal(0, lockw*0.5)
                end = tipf * rng.uniform(0.82, 1.0)
                b = max(0.0, rng.normal(0.030, 0.020)) + (0.07 if rng.random() < 0.08 else 0.0); sig = rng.uniform(0.4, 0.7)
                rows = np.arange(int(end*(H-1)) + 1); t = rows/(H-1)
                conv = np.clip((t / max(end, 1e-3)), 0, 1)**1.5      # strands gather toward the lock tip
                xc = c + off*(1 - 0.85*conv) + 1.5*np.sin(t*9 + off)
                fade = np.clip((end - t)/(p['taper']*end), 0, 1)**0.8
                for dx in range(-2, 3):
                    xi = np.floor(xc).astype(int) + dx
                    wgt = np.exp(-0.5*((xi + 0.5 - xc)/sig)**2)*fade
                    xi = np.clip(xi, 0, W-1)
                    np.add.at(acc, (rows, xi), wgt*b); np.add.at(cov, (rows, xi), wgt)
        dens = np.clip(cov/1.2, 0, 1)
        if p.get('wisp'):
            # individual strands only (no solid sheet), long root fade: soft hairline wisps
            t_ = np.clip(ys/0.45, 0, 1); root = (t_*t_*(3 - 2*t_))[:, None]
            alpha = np.clip(dens*1.3, 0, 0.9)*root
            val = np.clip(BASE + acc*0.30, 0, 1)
        else:
            root = fc_root_fade(ys)[:, None]                              # alpha fade-in over the root band (FH54: longer)
            solid = np.clip(1 - (ys - 0.25)/0.35, 0, 1)[:, None]      # solid sheet near root, locks below
            alpha = np.clip(np.maximum(dens, solid*0.97), 0, 1)*root
            val = np.clip(BASE + acc*0.21, 0, 1)
        edge = np.clip(np.minimum(np.arange(W), W - 1 - np.arange(W))/3.0, 0, 1)[None, :]
        alpha = alpha*edge                                          # no hard alpha at strip borders
        rgba[:, x0:x1, 0] = val; rgba[:, x0:x1, 1] = val*0.97; rgba[:, x0:x1, 2] = val*0.95
        rgba[:, x0:x1, 3] = alpha
    Image.fromarray((np.clip(rgba, 0, 1)*255 + 0.5).astype(np.uint8), 'RGBA').save(out)
    return {'alpha_mean': float(rgba[..., 3].mean().round(4))}


def make_edge(out, W=512, H=256):
    """FH54 hairline edge texture for the CapEdge band. u tiles along the hairline, v = 0 at the hairline .. 1 at
    the inner end of the feather. Strands run along v and end at random heights, so the feathered hairline
    breaks into individual strand tips instead of a smooth painted fade."""
    rng = np.random.default_rng(5303)
    acc = np.zeros((H, W)); cov = np.zeros((H, W)); ys = np.arange(H)/(H - 1)      # row 0 = v 1 (inner), last = v 0
    for _ in range(1400):
        x0 = rng.uniform(0, W); end = rng.uniform(0.35, 1.0)**0.8                    # fraction of the band the strand reaches
        b = max(0.0, rng.normal(0.035, 0.02)) + (0.06 if rng.random() < 0.08 else 0.0); sig = rng.uniform(0.4, 0.7)
        rows = np.arange(int(end*(H - 1)) + 1); t = rows/(H - 1)
        xc = x0 + 1.2*np.sin(t*7 + x0)
        fade = np.clip((end - t)/(0.35*end), 0, 1)**0.8
        for dx in range(-2, 3):
            xi = np.floor(xc).astype(int) + dx; wgt = np.exp(-0.5*((xi + 0.5 - xc)/sig)**2)*fade
            np.add.at(acc, (rows, xi % W), wgt*b); np.add.at(cov, (rows, xi % W), wgt)
    dens = np.clip(cov/1.0, 0, 1)
    solid = np.clip(1 - (ys - 0.10)/0.35, 0, 1)[:, None]                              # inner part stays opaque
    alpha = np.clip(np.maximum(dens, solid), 0, 1)
    val = np.clip(BASE + acc*0.22, 0, 1)
    img = np.stack([val, val*0.97, val*0.95, alpha], -1)
    Image.fromarray((img*255 + 0.5).astype(np.uint8), 'RGBA').save(out)
    return {'alpha_mean': float(alpha.mean().round(4))}


if __name__ == '__main__':
    o = Path(sys.argv[1]); o.mkdir(parents=True, exist_ok=True)
    print({'cap': make_cap(o/'TMH55_CAP_STRANDS_512.png'), 'cards': make_cards(o/'TMH55_CARD_STRANDS_512.png'),
           'edge': make_edge(o/'TMH55_EDGE_STRANDS_512x256.png')})
