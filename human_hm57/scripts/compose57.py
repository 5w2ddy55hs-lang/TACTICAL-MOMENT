"""HM56 -> HM57 (+ LITE) comparison sheets for iPhone (1080 px wide; columns HM56 | HM57 | HM57 LITE, same camera / pose /
light). Pixels are pasted from the real renders in renders/COMPARE; nothing is synthesised. Writes $HM_BUILD/images/S*.jpg.
If renders/RESEARCH_PRIVATE exists, a separate review sheet with the research reference is written to
renders/RESEARCH_PRIVATE/P01_target_comparison_PRIVATE.jpg (never to images/, never to git, never to the public ZIP)."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageFont
import hm_common as hc

R = hc.BUILD/'renders/COMPARE'; RP = hc.BUILD/'renders/RESEARCH_PRIVATE'; OUT = hc.BUILD/'images'; OUT.mkdir(parents=True, exist_ok=True)
FONT = next((f for f in ('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',) if os.path.exists(f)), None)
font = lambda n: ImageFont.truetype(FONT, n) if FONT else ImageFont.load_default()
BG = (22, 26, 34); FG = (238, 238, 230); SUB = (190, 196, 210); COL = {'HM56': (255, 170, 120), 'HM57': (140, 220, 160), 'HM57L': (140, 190, 255), '参照': (230, 200, 120)}
NAME = {'HM56': 'HM56 改善前', 'HM57': 'HM57 今回', 'HM57L': 'HM57 軽量版'}
MODELS = ('HM56', 'HM57', 'HM57L')


def load(p, cell, nearest=False, crop=None):
    im = Image.open(p).convert('RGB')
    if crop:
        W, H = im.size; cw, ch = crop; im = im.crop(((W - cw)//2, (H - ch)//2, (W + cw)//2, (H + ch)//2))
    return im.resize(cell, Image.NEAREST if nearest else Image.LANCZOS) if im.size != cell else im


def sheet(title, note, rows, cell, out, nearest=False, crop=None, folder=OUT):
    """rows: list of (row label, [(path, caption), ...])."""
    cols = max(len(r[1]) for r in rows); W = cell[0]*cols; head = 96; lab = 34
    img = Image.new('RGB', (W, head + len(rows)*(cell[1] + lab)), BG); dr = ImageDraw.Draw(img)
    dr.text((16, 12), title, fill=FG, font=font(30)); dr.text((16, 56), note, fill=SUB, font=font(17))
    for r, (rl, items) in enumerate(rows):
        y = head + r*(cell[1] + lab)
        for c, (p, cap) in enumerate(items):
            x = c*cell[0]; col = next((v for k, v in COL.items() if cap.startswith(NAME.get(k, k))), FG)
            dr.text((x + 8, y + 7), f'{rl}  {cap}'.strip(), fill=col, font=font(17))
            p = Path(p)
            if not p.exists():
                dr.text((x + 10, y + lab + 20), 'MISSING ' + p.name, fill=(255, 90, 90), font=font(14)); continue
            img.paste(load(p, cell, nearest, crop), (x, y + lab))
            if c:
                dr.line([(x, y), (x, y + lab + cell[1])], fill=(60, 66, 80), width=2)
    folder.mkdir(parents=True, exist_ok=True); img.save(folder/out, quality=90); return folder/out


def player_px(p):
    """Measured height (px) of the player in a pitch render: rows holding non-grass pixels (grass = green-dominant)."""
    import numpy as np
    a = np.asarray(Image.open(p).convert('RGB'), float)/255.0; m = ~((a[..., 1] > a[..., 0] + 0.04) & (a[..., 1] > a[..., 2] + 0.04)); rows = np.where(m.sum(1) > 0)[0]
    return int(rows.max() - rows.min() + 1) if len(rows) else 0


trio = lambda d, name: [(R/d/f'{m}_{name}.png', NAME[m]) for m in MODELS]
VN = {'front': '正面', 'side_L': '横', 'quarter_L': '斜め', 'back': '背面', 'low': '下から'}
sheet('全身：HM56 → HM57 → 軽量版', '代表 P0。同じカメラ・照明・A ポーズ。HM57 は髪 H1、袖の色の切り替え入り。', [(VN[v], trio('BODY', v)) for v in ('front', 'side_L', 'quarter_L', 'back')], (360, 720), 'S01_fullbody.jpg')
sheet('顔：HM56 → HM57 → 軽量版', '顔の下半分を細く、顎を締め、頬の張りを抑えた。軽量版は頭 900 三角形。', [(VN[v], trio('FACE', v)) for v in ('front', 'quarter_L', 'side_L', 'low')], (360, 360), 'S02_face.jpg')
sheet('首・肩・胸', '胴の厚み、袖の色の切り替え（ラグラン）、首の筋をやわらげた。', [(n, trio('PARTS', k)) for k, n in (('neck_front', '正面'), ('neck_quarter', '斜め'), ('neck_side', '横'), ('neck_back', '背面'))], (360, 360), 'S03_neck_shoulder.jpg')
sheet('脚・スパイク', '太もも・ふくらはぎを太く。ソックスの口を 12mm 下げた。', [(n, trio('PARTS', k)) for k, n in (('legs_front', '脚 正面'), ('legs_side', '脚 横'), ('legs_quarter', '脚 斜め'), ('boot_side', 'スパイク 横'))], (360, 360), 'S04_legs_boots.jpg')
neck = [('turn_left', '左を向く'), ('turn_right', '右を向く'), ('look_up', '見上げる'), ('look_down', 'うつむく'), ('tilt', '傾ける'), ('header', 'ヘディング'), ('throw', 'スローイン')]
sheet('動作中の首と襟（正面）', '首振り・ヘディング・スローインの同じコマ。', [(n, trio('NECKMOTION', f'{k}_front')) for k, n in neck], (360, 360), 'S05_neck_in_motion_front.jpg')
sheet('動作中の首と襟（背面）', '同じコマを背面から。', [(n, trio('NECKMOTION', f'{k}_back')) for k, n in neck], (360, 360), 'S05b_neck_in_motion_back.jpg')
jt = [('armpit_kick', 'front', '脇（蹴る）'), ('armpit_kick', 'side_low', '脇（蹴る・下）'), ('armpit_throw', 'front', '脇（スローイン）'), ('armpit_throw', 'side_low', '脇（スローイン・下）'),
      ('knee_run', 'side_L', '膝裏（走る）'), ('knee_kick', 'side_L', '膝裏（蹴る）'), ('knee_kick', 'back_quarter', '膝裏（蹴る・後ろ）'), ('knee_header', 'side_L', '膝裏（踏切）')]
sheet('動作中の脇・膝裏（貫通と隙間の確認）', '同じコマ・同じカメラ。', [(n, trio('NECKMOTION', f'{k}_{v}')) for k, v, n in jt], (360, 360), 'S06_armpit_knee_in_motion.jpg')
acts = [('Run', [0, 5, 10, 15], '走る'), ('Kick', [8, 14, 19, 25], '蹴る'), ('Header', [9, 17, 21, 30], 'ヘディング'), ('LookAround', [15, 45, 70, 80], '首振り'), ('ThrowIn', [0, 13, 20, 29], 'スローイン')]
rows = []
for a, fr, jn in acts:
    for m in MODELS:
        rows.append((jn, [(R/'MOTION'/f'{m}_{a}_{f:03d}_quarter_L.png', f'{NAME[m]} {f}') for f in fr]))
sheet('5 動作の同じコマ（斜め）', '各動作 3 段：HM56 / HM57 / 軽量版。HM57 は接地を修正（足が地面に沈まない）。連続再生は動画を参照。', rows, (270, 432), 'S07_motion_frames.jpg')
PH = player_px(R/'MATCH'/'HM57_broadcast_stand.png') if (R/'MATCH'/'HM57_broadcast_stand.png').exists() else 0
PHP = player_px(R/'PHONE'/'HM57_phone_run.png') if (R/'PHONE'/'HM57_phone_run.png').exists() else 0
sheet('試合中の距離（中継カメラ：約25m・高さ12m・85mm）', f'1280×720 の画面全体を縮小。立ち姿の選手の高さは画面で {PH} 画素（実測）。',
      [(lab, trio('MATCH', f'broadcast_{k}')) for k, lab in (('stand', '立ち'), ('run', '走る'), ('kick', '蹴る'), ('header', 'ヘディング'))], (360, 203), 'S08_match_full_frame.jpg')
CW, CH = int(PH*0.8) or 120, int(PH*1.25) or 150
sheet('試合距離の拡大（実際の画素を拡大）', f'中継画面 1280×720 の選手まわり {CW}×{CH} 画素を、最近傍で拡大しただけ（選手の高さ {PH} 画素）。',
      [(lab, trio('MATCH', f'broadcast_{k}')) for k, lab in (('stand', '立ち'), ('run', '走る'), ('kick', '蹴る'), ('header', 'ヘディング'))], (360, int(360*CH/CW)), 'S09_match_zoom.jpg', nearest=True, crop=(CW, CH))
sheet('リプレイ（3.6m・50mm）', 'リプレイ風の近いカメラ。選手まわりを切り出し。', [(lab, trio('REPLAY', f'replay_{k}')) for k, lab in (('kick', '蹴る'), ('header', 'ヘディング'), ('run', '走る'), ('throw', 'スローイン'))],
      (360, 405), 'S10_replay.jpg', crop=(480, 540))
sheet('スマホ画面（iPhone 横向き 844×390pt、3倍＝2532×1170 画素）', f'試合カメラ 25m・50mm（広め）。選手の高さ {PHP} 画素（約 {PHP//3}pt）。選手まわり 300×300 画素（＝100×100pt）をそのまま拡大。',
      [(lab, trio('PHONE', f'phone_{k}')) for k, lab in (('run', '走る'), ('kick', '蹴る'))], (360, 360), 'S11_phone_screen.jpg', crop=(300, 300))
sheet('小さい表示（その画素数で描画）', '選手の高さ 32・48・72・96 画素で描画したものを最近傍で拡大。', [(f'高さ{px}px', trio('SMALL', f'{px}px_run')) for px in (32, 48, 72, 96)], (360, 720), 'S12_small_sizes.jpg', nearest=True)
# full phone frame (HM57) for context
p = R/'PHONE'/'HM57_phone_run.png'
if p.exists():
    sheet('スマホ画面の全体（HM57、縮小表示）', '2532×1170 の画面を縮小しています。選手の実際の大きさの目安。', [('', [(p, NAME['HM57'])])], (1080, 499), 'S11b_phone_full_frame.jpg')
# ---- private target comparison (research reference) - separate folder only
if RP.exists():
    quad = lambda d, name, ref: [(RP/d/f'REF_{ref}.png', '参照（非公開）')] + [(R/d/f'{m}_{name}.png', NAME[m]) for m in MODELS]
    rows = [('全身 正面', quad('BODY', 'front', 'front')), ('全身 横', quad('BODY', 'side_L', 'side_L')), ('顔 正面', quad('FACE', 'front', 'front')), ('顔 斜め', quad('FACE', 'quarter_L', 'quarter_L')), ('顔 横', quad('FACE', 'side_L', 'side_L'))]
    sheet('目標との比較（研究用参照・非公開）', '左端は研究用参照（ゲーム由来・公開不可）。参照は静止ポーズのみ。', rows, (270, 405), 'P01_target_comparison_PRIVATE.jpg', folder=RP)
    rows = [('試合距離', [(RP/'MATCH'/'REF_broadcast_stand.png', '参照（非公開）')] + [(R/'MATCH'/f'{m}_broadcast_stand.png', NAME[m]) for m in MODELS]),
            ('スマホ', [(RP/'PHONE'/'REF_phone_stand.png', '参照（非公開）')] + [(R/'PHONE'/f'{m}_phone_run.png', NAME[m]) for m in MODELS])]
    sheet('目標との比較：試合距離（非公開）', '中継画面の選手まわりを最近傍で拡大。すべて立ち姿。', rows[:1], (270, int(270*CH/CW)), 'P02_target_match_PRIVATE.jpg', nearest=True, crop=(CW, CH), folder=RP)
    sheet('目標との比較：スマホ画面（非公開）', '選手まわり 300×300 画素。', rows[1:], (270, 270), 'P03_target_phone_PRIVATE.jpg', crop=(300, 300), folder=RP)
    sheet('目標との比較：小さい表示（非公開）', 'その画素数で描画。', [(f'高さ{px}px', [(RP/'SMALL'/f'REF_{px}px_run.png', '参照（非公開）')] + [(R/'SMALL'/f'{m}_{px}px_run.png', NAME[m]) for m in MODELS]) for px in (48, 72)],
          (270, 540), 'P04_target_small_PRIVATE.jpg', nearest=True, folder=RP)
print('sheets', len(list(OUT.glob('S*.jpg'))), 'private', len(list(RP.glob('P*.jpg'))) if RP.exists() else 0)
