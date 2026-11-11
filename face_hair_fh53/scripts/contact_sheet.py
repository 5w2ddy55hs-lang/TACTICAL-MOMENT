"""Compose rendered PNGs into a labelled comparison sheet (no image synthesis; pixels are pasted as-is)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw


def sheet(rows, cols, path_fn, out, cell=256, label_fn=None, col_labels=None):
    pad = 18
    W = cell*len(cols); H = (cell + pad)*len(rows) + (pad if col_labels else 0)
    img = Image.new('RGB', (W, H), (24, 28, 36)); dr = ImageDraw.Draw(img)
    y0 = 0
    if col_labels:
        for c, lab in enumerate(col_labels):
            dr.text((c*cell + 4, 3), lab, fill=(230, 230, 230))
        y0 = pad
    for r, row in enumerate(rows):
        y = y0 + r*(cell + pad)
        dr.text((4, y + 3), label_fn(row) if label_fn else str(row), fill=(240, 240, 200))
        for c, col in enumerate(cols):
            p = Path(path_fn(row, col))
            if p.exists():
                im = Image.open(p).convert('RGB')
                if im.size != (cell, cell):
                    im = im.resize((cell, cell), Image.LANCZOS)
                img.paste(im, (c*cell, y + pad))
            else:
                dr.text((c*cell + 10, y + pad + cell//2), 'MISSING', fill=(255, 80, 80))
    Path(out).parent.mkdir(parents=True, exist_ok=True); img.save(out, quality=92)
    return out


if __name__ == '__main__':
    d, out = Path(sys.argv[1]), sys.argv[2]; rows = sys.argv[3].split(','); cols = sys.argv[4].split(',')
    sheet(rows, cols, lambda r, c: d/f'{r}_{c}.png', out, col_labels=cols)
