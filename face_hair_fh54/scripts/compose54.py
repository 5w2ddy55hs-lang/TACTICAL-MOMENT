"""FH54 comparison sheets (pixels pasted from real renders; nothing synthesised). Phone-friendly sheets are
1080 px wide. Labels use IPA Gothic when available. Writes build/images/*.jpg."""
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import fh53_common as fc

R = fc.BUILD/'renders'; OUT = fc.BUILD/'images'; OUT.mkdir(parents=True, exist_ok=True)
FONT = next((f for f in ('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf') if os.path.exists(f)), None)
def font(sz):
    return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()
BG = (22, 26, 34); FG = (238, 238, 230); SUB = (190, 196, 210)


def grid(path, title, rows, cols, cell, out, note=None, nearest=False, row_labels=None, col_labels=None, cell_labels=None):
    """rows x cols of image paths (None = empty). cell=(w,h)."""
    W = cell[0]*cols; head = 64 if note else 48; lab = 30
    H = head + len(rows)*(cell[1] + lab)
    img = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(img)
    dr.text((16, 10), title, fill=FG, font=font(26))
    if note:
        dr.text((16, 40), note, fill=SUB, font=font(16))
    for r, row in enumerate(rows):
        y = head + r*(cell[1] + lab)
        for c, p in enumerate(row):
            x = c*cell[0]
            text = (col_labels[c] if col_labels else '') if not row_labels else f'{row_labels[r]}  {col_labels[c] if col_labels else ""}'
            if cell_labels:
                text = cell_labels[r][c]
            dr.text((x + 6, y + 5), text.strip(), fill=FG, font=font(17))
            if p is None:
                continue
            p = Path(p)
            if not p.exists():
                dr.text((x + 10, y + lab + cell[1]//2), 'MISSING ' + p.name, fill=(255, 90, 90), font=font(14)); continue
            im = Image.open(p).convert('RGB')
            im = im.resize(cell, Image.NEAREST if nearest else Image.LANCZOS) if im.size != cell else im
            img.paste(im, (x, y + lab))
    img.save(OUT/out, quality=90)
    return OUT/out


def main():
    S = R/'SEVEN_faces'; Hs = R/'SEVEN_hairs'; Cl = R/'CLOSEUPS'; Sm = R/'SMALL'; Fb = R/'FACE_BREAKDOWN'; Co = R/'COMBOS'
    faces = [('FACE52', 'F0 原本'), ('FH54_F1_H0', 'F1 面長・角顎'), ('FH54_F2_H0', 'F2 丸顔'), ('FH54_F3_H0', 'F3 細面')]
    note_same = '同じカメラ・照明・距離（FACE52の確認用設定）。書き出したGLBを空シーンへ読み込んで描画。'
    grid(None, 'FH54 顔の比較（髪はH0原本で統一）', [[S/f'{k}_{v}.png' for k, _ in faces] for v in ('front', 'quarter_R', 'side_R', 'quarter_L')],
         4, (270, 270), 'M01_faces_FH54.jpg', note=note_same, row_labels=['正面', '右斜め', '右側面', '左斜め'], col_labels=[n for _, n in faces])
    rows = []
    for f in ('F1', 'F2', 'F3'):
        rows.append([S/f'FH53_{f}_H0_front.png', S/f'FH54_{f}_H0_front.png', S/f'FH53_{f}_H0_quarter_R.png', S/f'FH54_{f}_H0_quarter_R.png'])
    grid(None, '顔 FH53 → FH54（変更前後・同条件）', rows, 4, (270, 270), 'M02_faces_before_after.jpg', note=note_same,
         row_labels=['F1', 'F2', 'F3'], col_labels=['FH53 正面', 'FH54 正面', 'FH53 斜め', 'FH54 斜め'])
    rows = [[Fb/f'F0_H0_face_front.png', Fb/f'{f}S_H0_face_front.png', Fb/f'{f}T_H0_face_front.png', Fb/f'{f}_H0_face_front.png'] for f in ('F1', 'F2', 'F3')]
    grid(None, '顔の内訳：形だけ／テクスチャだけ／両方', rows, 4, (270, 270), 'M03_face_breakdown.jpg',
         note='左から F0原本・形だけ変更・テクスチャだけ変更・完成形（同照明・同角度）', row_labels=['F1', 'F2', 'F3'], col_labels=['F0', '形', 'テクスチャ', '両方'])
    rows = [[Fb/f'F0_H2_face_quarterR.png', Fb/f'{f}S_H2_face_quarterR.png', Fb/f'{f}T_H2_face_quarterR.png', Fb/f'{f}_H2_face_quarterR.png'] for f in ('F1', 'F2', 'F3')]
    grid(None, '顔の内訳（短髪H2・斜め：耳と額が見える条件）', rows, 4, (270, 270), 'M03b_face_breakdown_H2_quarter.jpg', note='耳はF1〜F3で形を修正、F0は原本のまま', row_labels=['F1', 'F2', 'F3'], col_labels=['F0', '形', 'テクスチャ', '両方'])
    small = ['FACE52', 'FH54_F1_H1', 'FH54_F2_H2', 'FH54_F3_H3']
    rows = [[Sm/f'{k}_{px}px_front.png' for k in small] for px in (64, 96, 128)]
    grid(None, '小さい表示サイズ（選手一覧・試合を想定）', rows, 4, (270, 270), 'M04_small_size.jpg',
         note='64／96／128 pxで描画した画像をそのまま拡大（最近傍）。縮小ではなく実寸描画。', nearest=True,
         row_labels=['64px', '96px', '128px'], col_labels=['FACE52', 'F1×H1', 'F2×H2', 'F3×H3'])
    rows = [[Sm/f'{k}_{px}px_front.png' for k in ('FACE52', 'FH54_F1_H0', 'FH54_F2_H0', 'FH54_F3_H0')] for px in (64, 128)]
    grid(None, '小さい表示：顔だけの違い（髪はH0で統一）', rows, 4, (270, 270), 'M04b_small_size_faces_only.jpg', nearest=True,
         row_labels=['64px', '128px'], col_labels=['F0', 'F1', 'F2', 'F3'])
    rows = [[Hs/f'FH53_F0_{h}_front.png', Hs/f'FH54_F0_{h}_front.png', Hs/f'FH53_F0_{h}_side_R.png', Hs/f'FH54_F0_{h}_side_R.png'] for h in ('H1', 'H2', 'H3', 'H4')]
    grid(None, '髪 FH53 → FH54（顔はF0原本で統一）', rows, 4, (270, 270), 'M05_hairs_before_after.jpg', note=note_same,
         row_labels=['H1', 'H2', 'H3', 'H4'], col_labels=['FH53 正面', 'FH54 正面', 'FH53 側面', 'FH54 側面'])
    rows = [[Hs/f'FH53_F0_{h}_back.png', Hs/f'FH54_F0_{h}_back.png', Hs/f'FH53_F0_{h}_top.png', Hs/f'FH54_F0_{h}_top.png'] for h in ('H1', 'H2', 'H3', 'H4')]
    grid(None, '髪 FH53 → FH54：背面・上から', rows, 4, (270, 270), 'M06_hairs_back_top.jpg', note=note_same,
         row_labels=['H1', 'H2', 'H3', 'H4'], col_labels=['FH53 背面', 'FH54 背面', 'FH53 上', 'FH54 上'])
    probs = [('H1', 'ear_L', 'H1 耳の上'), ('H2', 'ear_R', 'H2 もみあげ'), ('H2', 'front_edge', 'H2 前の生え際'), ('H3', 'front_edge', 'H3 前の生え際'),
             ('H3', 'ear_R', 'H3 耳前'), ('H4', 'ear_R', 'H4 耳周り'), ('H4', 'front_edge', 'H4 前髪'), ('H2', 'nape', 'H2 襟足')]
    rows = [[Cl/f'FH53_F0_{h}_grazing_{v}.png', Cl/f'FH54_F0_{h}_grazing_{v}.png'] for h, v, _ in probs]
    grid(None, '問題箇所の拡大（斜光 grazing）FH53 → FH54', rows, 2, (540, 540), 'M07_problem_closeups_grazing.jpg',
         note='FACE52の grazing 設定。左 FH53／右 FH54', row_labels=[n for _, _, n in probs], col_labels=['FH53', 'FH54'])
    rows = [[Cl/f'FH53_F0_{h}_studio_{v}.png', Cl/f'FH54_F0_{h}_studio_{v}.png'] for h, v, _ in probs]
    grid(None, '問題箇所の拡大（studio）FH53 → FH54', rows, 2, (540, 540), 'M07b_problem_closeups_studio.jpg',
         row_labels=[n for _, _, n in probs], col_labels=['FH53', 'FH54'])
    rf = R/'ref04'; combos = [('REF04_original', 'Reference04 自身の頭'), ('F0_H0', 'FACE52'), ('F1_H1', 'F1×H1'), ('F2_H2', 'F2×H2'), ('F3_H3', 'F3×H3'), ('F2_H4', 'F2×H4')]
    rows = [[rf/f'{k}_body_front.png' for k, _ in combos[i:i+3]] for i in (0, 3)]
    names = [[n for _, n in combos[i:i+3]] for i in (0, 3)]
    grid(None, '全身の比較（Reference04に仮置き・接合なし）', rows, 3, (360, 720), 'M08_fullbody.jpg', note='頭の大きさ・首まわりの釣り合いの確認用。静止状態。胴体の肌色は未変更。',
         cell_labels=names)
    rows = [[rf/f'{k}_head_front.png' for k, _ in combos[i:i+3]] for i in (0, 3)] + [[rf/f'{k}_head_side.png' for k, _ in combos[i:i+3]] for i in (0, 3)]
    grid(None, '全身比較：頭と首の拡大（正面・側面）', rows, 3, (360, 360), 'M08b_fullbody_head_neck.jpg',
         cell_labels=[[f'{v} {n}' for n in names[i % 2]] for i, v in enumerate(['正面', '正面', '側面', '側面'])])
    an = R/'anim'
    rows = [[an/'RIGID_id1012_worst_f03_neck_back.png', an/'WEIGHTED_id1012_worst_f01_neck_back.png'],
            [an/'RIGID_id0039_worst_f45_neck_back.png', an/'WEIGHTED_id0039_worst_f45_neck_back.png'],
            [an/'RIGID_id1012_worst_f03_neck_front.png', an/'WEIGHTED_id1012_worst_f01_neck_front.png']]
    grid(None, '首の動き：仮の固定接続 と 仮のウェイト転写', rows, 2, (540, 540), 'M09_neck_motion.jpg',
         note='既存動作 id1012／id0039 の継ぎ目が最大になるフレーム。左 固定（頭ボーンに親子付け）／右 ウェイト転写', row_labels=['id1012 背面', 'id0039 背面', 'id1012 正面'], col_labels=['固定', 'ウェイト'])
    fo = fc.BUILD/'webtest/force'
    rows = []
    for m in ('FH53_H4', 'FH54_H4', 'FH53_H1', 'FH54_H1'):
        a = fo/f'{m}_back_cardsLast.png'; b = fo/f'{m}_back_cardsFirst.png'
        if a.exists() and b.exists():
            A = np.asarray(Image.open(a).convert('RGB')).astype(float); Bm = np.asarray(Image.open(b).convert('RGB')).astype(float)
            dmap = np.clip(np.abs(A - Bm).sum(2)/3*6, 0, 255).astype(np.uint8)
            hp = OUT/f'_diff_{m}.png'; Image.fromarray(np.stack([dmap, dmap//3, dmap//3], -1)).save(hp)
            rows.append([a, b, hp])
    grid(None, '透過の描画順を最悪に入れ替えたとき（three.js）', rows, 3, (360, 360), 'M10_transparency_order.jpg',
         note='左 毛束を後に描画／中 毛束を先に描画（最悪）／右 差分×6。FH54はcap内部を不透明化。', row_labels=['FH53 H4', 'FH54 H4', 'FH53 H1', 'FH54 H1'], col_labels=['通常', '最悪順', '差分'])
    # desktop: all 20 combinations
    F = ['F0', 'F1', 'F2', 'F3']; Hh = ['H0', 'H1', 'H2', 'H3', 'H4']
    for v, jp in (('front', '正面'), ('quarter_R', '右斜め'), ('back', '背面')):
        rows = [[Co/f'FH54_{f}_{h}_{v}.png' for h in Hh] for f in F]
        grid(None, f'顔4×髪5＝20組（{jp}）', rows, 5, (256, 256), f'D01_combos20_{v}.jpg', row_labels=['F0原本', 'F1', 'F2', 'F3'],
             col_labels=['H0原本', 'H1', 'H2', 'H3', 'H4'])
    print('SHEETS', sorted(p.name for p in OUT.glob('*.jpg')))


if __name__ == '__main__':
    main()
