"""HM55 comparison sheets (pixels pasted from real renders; nothing synthesised). Phone sheets are 1080 px wide.
Writes $HM_BUILD/images/*.jpg."""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageFont
import hm_common as hc

R = hc.BUILD/'renders'; OUT = hc.BUILD/'images'; OUT.mkdir(parents=True, exist_ok=True)
FONT = next((f for f in ('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf') if os.path.exists(f)), None)
font = lambda sz: ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()
BG = (22, 26, 34); FG = (238, 238, 230); SUB = (190, 196, 210)


def grid(title, rows, cell, out, note=None, labels=None, nearest=False):
    """rows: list of rows of image paths (None = empty). labels: same shape, text drawn above each cell."""
    cols = max(len(r) for r in rows); W = cell[0]*cols; head = 70 if note else 50; lab = 28
    img = Image.new('RGB', (W, head + len(rows)*(cell[1] + lab)), BG); dr = ImageDraw.Draw(img); dr.text((14, 10), title, fill=FG, font=font(25))
    if note:
        dr.text((14, 43), note, fill=SUB, font=font(15))
    for r, row in enumerate(rows):
        y = head + r*(cell[1] + lab)
        for c, p in enumerate(row):
            x = c*cell[0]
            if labels and labels[r][c]:
                dr.text((x + 5, y + 5), labels[r][c], fill=FG, font=font(16))
            if p is None:
                continue
            p = Path(p)
            if not p.exists():
                dr.text((x + 8, y + lab + cell[1]//2), 'MISSING ' + p.name, fill=(255, 90, 90), font=font(13)); continue
            im = Image.open(p).convert('RGB'); im = im.resize(cell, Image.NEAREST if nearest else Image.LANCZOS) if im.size != cell else im; img.paste(im, (x, y + lab))
    img.save(OUT/out, quality=90); return OUT/out


REP = [('P0_H2', 'P0×H2'), ('P1_H1', 'P1×H1'), ('P2_H4', 'P2×H4'), ('P3_H3', 'P3×H3')]
VN = {'front': '正面', 'quarter_L': '斜め', 'side_L': '側面', 'back': '背面', 'top': '上', 'above': '上から', 'back_quarter': '斜め後ろ'}
# M01 full body, rest pose
rows = [[R/'REST'/f'{c}_{v}.png' for c, _ in REP] for v in ('front', 'side_L', 'back')]
grid('HM55 独自モデル：全身（静止・A ポーズ）', rows, (270, 540), 'M01_fullbody_rest.jpg', note='書き出した GLB を読み直して描画。形・テクスチャ・骨はすべてスクリプト生成。',
     labels=[[f'{n} {VN[v]}' for _, n in REP] for v in ('front', 'side_L', 'back')])
# M02 faces
rows = [[R/'FACES'/f'{f}_{v}.png' for f in ('P0', 'P1', 'P2', 'P3')] for v in ('front', 'quarter_L', 'side_L')]
grid('HM55 顔 4 種（髪は H2 で統一、同じカメラ・照明）', rows, (270, 270), 'M02_faces.jpg', labels=[[f'{f} {VN[v]}' for f in ('P0 基準', 'P1 面長', 'P2 丸顔', 'P3 細面')] for v in ('front', 'quarter_L', 'side_L')])
# M03 hairs
rows = [[R/'HAIRS'/f'{h}_{v}.png' for v in ('front', 'side_L', 'back', 'top')] for h in ('H1', 'H2', 'H3', 'H4')]
grid('HM55 髪 4 種（顔は P0 で統一）', rows, (270, 270), 'M03_hairs.jpg', labels=[[f'{h} {VN[v]}' for v in ('front', 'side_L', 'back', 'top')] for h in ('H1', 'H2', 'H3', 'H4')])
# M04 ears / hairline close-ups
rows = [[R/'HAIRS'/f'{h}_{v}.png' for v in ('ear_L', 'ear_R', 'behind_ear_L', 'nape')] for h in ('H1', 'H2', 'H3', 'H4')]
grid('HM55 耳まわりと生え際の拡大', rows, (270, 270), 'M04_ears_hairline.jpg', note='左耳・右耳・耳の後ろ・襟足。髪の縁が浮いていないか、耳と交差していないかの確認用。',
     labels=[[f'{h} {n}' for n in ('左耳', '右耳', '耳の後ろ', '襟足')] for h in ('H1', 'H2', 'H3', 'H4')])
# M05 motion
acts = [('Run', [0, 5, 10, 15], '走る'), ('Kick', [8, 14, 19, 25], '蹴る'), ('ThrowIn', [0, 13, 20, 29], 'スローイン'), ('Header', [9, 17, 21, 30], 'ヘディング')]
rows = []; labs = []
for a, fr, jn in acts:
    for v in ('quarter_L', 'side_L'):
        rows.append([R/'MOTION'/f'{a}_{f:03d}_{v}.png' for f in fr]); labs.append([f'{jn} {f}コマ目 {VN[v]}' for f in fr])
grid('HM55 独自のサッカー動作（P1×H1、30 コマ/秒）', rows, (270, 432), 'M05_motion.jpg', note='動作は hm_anim.py の姿勢表から作成。ゲーム由来の動作データは使っていません。速度は検討用の仮の値。', labels=labs)
rows = [[R/'MOTION'/f'{a}_{f:03d}_back_quarter.png' for f in fr] for a, fr, jn in acts]
grid('HM55 動作：斜め後ろから', rows, (270, 432), 'M05b_motion_back.jpg', labels=[[f'{jn} {f}コマ目' for f in fr] for a, fr, jn in acts])
# M06 neck in motion
poses = [('rest', '静止'), ('turn_left', '左を向く'), ('turn_right', '右を向く'), ('up', '見上げる'), ('down', 'うつむく'), ('tilt', '傾けて回す'), ('header_strike', 'ヘディング'), ('throw_back', 'スローイン反り')]
for c, cn in (('P0_H2', 'P0×H2'), ('P2_H4', 'P2×H4')):
    rows = [[R/'NECK'/f'{c}_{p}_{v}.png' for v in ('front', 'side_L', 'back', 'above')] for p, _ in poses]
    grid(f'HM55 首の動き（{cn}）', rows, (270, 270), f'M06_neck_motion_{c}.jpg', note='首は頭部モジュール側にあり、襟の内側で胴体に固定。頭と胴体のあいだに肌の継ぎ目はありません。',
         labels=[[f'{pn} {VN[v]}' for v in ('front', 'side_L', 'back', 'above')] for _, pn in poses])
# M07 balance: research reference vs HM55 (same camera, same scale)
ref = R/'REFERENCE'
if (ref/'RESEARCH_FH54_F1_H1_on_Reference04_front.png').exists():
    rows = [[ref/f'RESEARCH_FH54_F1_H1_on_Reference04_{v}.png', R/'REST'/f'P1_H1_{v}.png'] for v in ('front', 'side_L', 'back')]
    grid('頭と体の釣り合い：研究用の参照と HM55（同じカメラ・縮尺）', rows, (540, 1080), 'M07_balance_vs_research.jpg', note='左は FH54 F1×H1 を Reference04 に載せた研究用（ゲーム由来・公開不可）。右は独自の HM55 P1×H1。',
         labels=[[f'研究用参照 {VN[v]}', f'HM55 {VN[v]}'] for v in ('front', 'side_L', 'back')])
    rows = [[ref/f'RESEARCH_neck_{v}.png', R/'NECK'/f'P0_H2_rest_{v}.png'] for v in ('front', 'side_L', 'back')]
    grid('首まわり：研究用の参照と HM55（静止）', rows, (540, 540), 'M07b_neck_vs_research.jpg', labels=[[f'研究用参照 {VN[v]}', f'HM55 {VN[v]}'] for v in ('front', 'side_L', 'back')])
# M08 small sizes and kit B
rows = [[R/'SMALL'/f'{c}_{px}px_front.png' for c, _ in REP] for px in (64, 96, 128)]
grid('HM55 小さい表示（実際にその画素数で描画）', rows, (270, 540), 'M08_small_sizes.jpg', nearest=True, labels=[[f'{n} 幅{px}px' for _, n in REP] for px in (64, 96, 128)])
rows = [[R/'KITS'/'P0_H1_KITB_front.png', R/'KITS'/'P0_H1_KITB_back.png', R/'KITS'/'P2_H3_KITB_front.png', R/'KITS'/'P2_H3_KITB_back.png']]
grid('HM55 ユニフォーム B（色違いの例）', rows, (270, 540), 'M09_kit_b.jpg', labels=[['P0×H1 正面', 'P0×H1 背面', 'P2×H3 正面', 'P2×H3 背面']])
# D01 all 16 combinations
combos = [[f'{f}_{h}' for h in ('H1', 'H2', 'H3', 'H4')] for f in ('P0', 'P1', 'P2', 'P3')]
grid('HM55 顔 4 × 髪 4 = 16 組（正面）', [[R/'ALL16'/f'{c}_front.png' for c in row] for row in combos], (270, 300), 'D01_all16_front.jpg', labels=[[c.replace('_', '×') for c in row] for row in combos])
grid('HM55 顔 4 × 髪 4 = 16 組（斜め）', [[R/'ALL16'/f'{c}_quarter_L.png' for c in row] for row in combos], (270, 300), 'D01_all16_quarter.jpg', labels=[[c.replace('_', '×') for c in row] for row in combos])
print('sheets', len(list(OUT.glob('*.jpg'))))
