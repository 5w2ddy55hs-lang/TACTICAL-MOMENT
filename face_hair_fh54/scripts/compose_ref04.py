"""Compose the Reference04 provisional review sheet from build/renders/ref04 (pixels pasted, not synthesised)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw
import fh53_common as fc
d = fc.BUILD/'renders/ref04'; out = fc.BUILD/'images'; out.mkdir(parents=True, exist_ok=True)
rows = ['REF04_original', 'F0_H0', 'F1_H1', 'F2_H2', 'F3_H3', 'F2_H4']
labels = {'REF04_original': 'Reference04 own head (reference)', 'F0_H0': 'FACE52 (F0xH0)'}
W = 384*len(rows); img = Image.new('RGB', (W, 18 + 768 + 3*(18 + 384)), (24, 28, 36)); dr = ImageDraw.Draw(img)
for c, r in enumerate(rows):
    dr.text((c*384 + 4, 3), labels.get(r, r), fill=(240, 240, 200))
    img.paste(Image.open(d/f'{r}_body_front.png').convert('RGB'), (c*384, 18))
    for k, shot in enumerate(('head_front', 'head_side', 'head_back')):
        y = 18 + 768 + k*(18 + 384)
        dr.text((c*384 + 4, y + 3), shot, fill=(200, 200, 200)); img.paste(Image.open(d/f'{r}_{shot}.png').convert('RGB'), (c*384, y + 18))
dr.text((4, img.size[1] - 14), 'PROVISIONAL static placement: not joined, no weights, not animated', fill=(255, 160, 120))
img.save(out/'REF04_PROVISIONAL_REVIEW.jpg', quality=90)
q = Image.new('RGB', (384*len(rows), 768 + 18), (24, 28, 36)); dq = ImageDraw.Draw(q)
for c, r in enumerate(rows):
    dq.text((c*384 + 4, 3), labels.get(r, r), fill=(240, 240, 200)); q.paste(Image.open(d/f'{r}_body_quarterR.png').convert('RGB'), (c*384, 18))
q.save(out/'REF04_PROVISIONAL_REVIEW_quarter.jpg', quality=90)
print('ok')
