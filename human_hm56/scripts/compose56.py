"""HM55 -> HM56 comparison sheets for iPhone (1080 px wide; left = before, right = after, same camera / pose / light).
Pixels are pasted from the real renders in renders/COMPARE; nothing is synthesised. Writes $HM_BUILD/images/C*.jpg."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageFont
import hm_common as hc

R = hc.BUILD/'renders/COMPARE'; OUT = hc.BUILD/'images'; OUT.mkdir(parents=True, exist_ok=True)
FONT = next((f for f in ('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',) if os.path.exists(f)), None)
font = lambda n: ImageFont.truetype(FONT, n) if FONT else ImageFont.load_default()
BG = (22, 26, 34); FG = (238, 238, 230); SUB = (190, 196, 210); OLD = (255, 170, 120); NEW = (140, 220, 160)


def sheet(title, note, rows, cell, out, nearest=False):
    """rows: list of (row label, [(path, caption), ...])."""
    cols = max(len(r[1]) for r in rows); W = cell[0]*cols; head = 96; lab = 34
    img = Image.new('RGB', (W, head + len(rows)*(cell[1] + lab)), BG); dr = ImageDraw.Draw(img)
    dr.text((16, 12), title, fill=FG, font=font(30)); dr.text((16, 56), note, fill=SUB, font=font(18))
    for r, (rl, items) in enumerate(rows):
        y = head + r*(cell[1] + lab)
        for c, (p, cap) in enumerate(items):
            x = c*cell[0]; col = OLD if cap.startswith('HM55') else NEW if cap.startswith('HM56') else FG
            dr.text((x + 8, y + 6), f'{rl}  {cap}'.strip(), fill=col, font=font(19))
            p = Path(p)
            if not p.exists():
                dr.text((x + 10, y + lab + 20), 'MISSING ' + p.name, fill=(255, 90, 90), font=font(14)); continue
            im = Image.open(p).convert('RGB'); im = im.resize(cell, Image.NEAREST if nearest else Image.LANCZOS) if im.size != cell else im; img.paste(im, (x, y + lab))
        dr.line([(cell[0]*cols//2, y), (cell[0]*cols//2, y + lab + cell[1])], fill=(60, 66, 80), width=2) if cols == 2 else None
    img.save(OUT/out, quality=90); return OUT/out


pair = lambda d, name: [(R/d/f'HM55_{name}.png', 'HM55 改良前'), (R/d/f'HM56_{name}.png', 'HM56 改良後')]
VN = {'front': '正面', 'side_L': '横', 'quarter_L': '斜め', 'back': '背面', 'low': '下から'}
sheet('全身：改良前 → 改良後', '代表 P0×H2。同じカメラ・照明・A ポーズ。左が HM55、右が HM56。', [(VN[v], pair('BODY', v)) for v in ('front', 'side_L', 'quarter_L', 'back')], (540, 1080), 'C01_fullbody_before_after.jpg')
sheet('顔：改良前 → 改良後', 'まぶた・頬骨・唇・顎を形状で追加。同じカメラ・照明。', [(VN[v], pair('FACE', v)) for v in ('front', 'quarter_L', 'side_L', 'low')], (540, 540), 'C02_face_before_after.jpg')
sheet('首から肩・胸・背中へのつながり', '首の付け根の筋肉と、首に沿う襟。肩当てのような肩を解消。', [(n, pair('PARTS', k)) for k, n in (('neck_front', '正面'), ('neck_quarter', '斜め'), ('neck_side', '横'), ('neck_back', '背面'))], (540, 540), 'C03_neck_shoulder_before_after.jpg')
sheet('膝・ふくらはぎ・足首・スパイク', 'ふくらはぎの2つの山、細い足首、低いつま先とソール。', [(n, pair('PARTS', k)) for k, n in (('legs_front', '脚 正面'), ('legs_side', '脚 横'), ('legs_quarter', '脚 斜め'), ('boot_side', 'スパイク 横'))], (540, 540), 'C04_legs_boots_before_after.jpg')
neck = [('turn_left', '左を向く'), ('turn_right', '右を向く'), ('look_up', '見上げる'), ('look_down', 'うつむく'), ('tilt', '傾ける'), ('header', 'ヘディング'), ('throw', 'スローイン')]
sheet('動作中の首と襟（正面・横）', '首振り・ヘディング・スローインの同じコマ。左2枚 HM55、右2枚 HM56。',
      [(n, [(R/'NECKMOTION'/f'HM55_{k}_front.png', 'HM55 正面'), (R/'NECKMOTION'/f'HM55_{k}_side_L.png', 'HM55 横'), (R/'NECKMOTION'/f'HM56_{k}_front.png', 'HM56 正面'), (R/'NECKMOTION'/f'HM56_{k}_side_L.png', 'HM56 横')]) for k, n in neck], (270, 270), 'C05_neck_in_motion.jpg')
sheet('動作中の首と襟（背面・上から）', '同じコマ。左2枚 HM55、右2枚 HM56。',
      [(n, [(R/'NECKMOTION'/f'HM55_{k}_back.png', 'HM55 背面'), (R/'NECKMOTION'/f'HM55_{k}_above.png', 'HM55 上'), (R/'NECKMOTION'/f'HM56_{k}_back.png', 'HM56 背面'), (R/'NECKMOTION'/f'HM56_{k}_above.png', 'HM56 上')]) for k, n in neck], (270, 270), 'C05b_neck_in_motion_back.jpg')
jt = [('armpit_kick', 'front', '脇（蹴る）'), ('armpit_kick', 'side_low', '脇（蹴る・下から）'), ('armpit_throw', 'front', '脇（スローイン）'), ('knee_run', 'side_L', '膝裏（走る）'), ('knee_kick', 'side_L', '膝裏（蹴る）'), ('knee_kick', 'back_quarter', '膝裏（蹴る・後ろ）'), ('knee_header', 'side_L', '膝裏（ヘディング踏切）')]
sheet('動作中の脇とシャツ、膝裏とソックス', '同じコマ・同じカメラ。左 HM55、右 HM56。', [(n, pair('NECKMOTION', f'{k}_{v}')) for k, v, n in jt], (540, 540), 'C06_armpit_knee_in_motion.jpg')
acts = [('Run', [0, 5, 10, 15], '走る'), ('Kick', [8, 14, 19, 25], '蹴る'), ('Header', [9, 17, 21, 30], 'ヘディング'), ('LookAround', [15, 45, 70, 80], '首振り'), ('ThrowIn', [0, 13, 20, 29], 'スローイン')]
rows = []
for a, fr, jn in acts:
    rows.append((jn, [(R/'MOTION'/f'HM55_{a}_{f:03d}_quarter_L.png', f'HM55 {f}コマ') for f in fr]))
    rows.append((jn, [(R/'MOTION'/f'HM56_{a}_{f:03d}_quarter_L.png', f'HM56 {f}コマ') for f in fr]))
sheet('6 動作の同じコマ（斜め）', '各動作の上段 HM55、下段 HM56。30 コマ/秒。連続再生は動画を参照。', rows, (270, 432), 'C07_motion_frames.jpg')
rows = [(lab, pair('MATCH', f'broadcast_{k}')) for k, lab in (('stand', '試合距離 立ち'), ('run', '試合距離 走る'), ('kick', '試合距離 蹴る'))]
sheet('試合中の距離（約25m、テレビ中継風の望遠）', '1280×720 で描画した全体。選手の身長は画面で約 90 画素。', rows, (540, 304), 'C08_match_distance.jpg')
# zoomed crops of the broadcast frames (nearest-neighbour, so the real pixels stay visible) + tiny direct renders
crops = []
for k in ('stand', 'run', 'kick'):
    for m in ('HM55', 'HM56'):
        p = R/'MATCH'/f'{m}_broadcast_{k}.png'
        if p.exists():
            im = Image.open(p).convert('RGB'); bb = Image.eval(im, lambda v: v).getbbox(); c = im.crop((560, 250, 720, 470)); c.save(R/'MATCH'/f'{m}_broadcast_{k}_crop.png')
rows = [(lab, pair('MATCH', f'broadcast_{k}_crop')) for k, lab in (('stand', '立ち'), ('run', '走る'), ('kick', '蹴る'))] + [(f'幅{px}px', pair('MATCH', f'{px}px_run')) for px in (48, 72, 96)]
sheet('試合距離の拡大（画素を拡大しただけ）', '上3段は中継風の画面の一部を拡大。下3段は実際にその画素数で描画。', rows, (540, 540), 'C09_match_distance_zoom.jpg', nearest=True)
print('sheets', len(list(OUT.glob('C*.jpg'))))
