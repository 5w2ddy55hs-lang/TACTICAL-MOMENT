# TACTICAL MOMENT 人間モデル HM57（試合演出向けの改訂候補）

**候補です。完成とは宣言していません。** 正式採用・公開・試合エンジンへの組み込みはしていません。詳細は [REPORT_JA.md](REPORT_JA.md)、ゲームに接続するための情報は [INTEGRATION_JA.md](INTEGRATION_JA.md)、実測値の表は `qa/QA_TABLES57.md` にあります。

- HM57 は、HM56 の生成スクリプトを `human_hm57/scripts/` に複製して編集し、作り直した代表 1 体（顔 P0 × 髪 H1 × ユニフォーム A）と、そのスマホ向け軽量版です。
- **HM55・HM56 の原本・スクリプト・検証結果は変更していません。** HM56 の GLB は比較の「改善前」として読むだけです。
- 研究用の参照モデル（サカつく2002 由来の Reference04）は、**目標との見比べの描画にだけ**使いました。生成の入力にはしていません。参照が写った画像は別の非公開 ZIP に分け、この ZIP と git には入れていません。
- 外部サービスへのアップロード、購入、API クレジットの使用はしていません。

## git に入れていないもの

- このリポジトリは公開（public）です。`.blend`・`.glb`・テクスチャ・画像・動画・ZIP は `human_hm57/build/`（`.gitignore` で除外）に置いています。
- git に入っているのは、スクリプト・報告書・数値だけの QA 記録（`qa/`）です。参照モデルに関する描画のログ行は除いています。

## ZIP の中身（`TM_HM57_MATCH_PLAYER_20261111.zip`）

| パス | 内容 |
|---|---|
| `models/players/TM_HM57_PLAYER_P0_H1_KITA.glb` | 代表選手（骨 22・動作 6） |
| `models/players/TM_HM57_PLAYER_P0_H1_KITA_LITE.glb` | 同じ選手のスマホ向け軽量版（骨・動作は同じ） |
| `models/players/*.blend`、`models/TM_HM57_LIBRARY.blend` | 編集用の原本 |
| `models/modules/` | 差し替え用の部品（胴体 A/B、頭、髪） |
| `textures/` | 生成したテクスチャ（通常版 PNG、軽量版 JPEG/PNG） |
| `images/S01〜S12_*.jpg` | **iPhone 向けの比較画像**（幅 1080px、列 = HM56 / HM57 / 軽量版） |
| `renders/COMPARE/` | 比較画像の元の描画（同じカメラ・姿勢・照明） |
| `video/` | 連続再生の動画（MP4 は H.264・yuv420p で iPhone 向けの形式）と GIF |
| `webtest/` | ブラウザ（three.js）での部品差し替え・同時描画の画像 |
| `qa/`、`logs/` | 検証の記録、実行ログ |
| `scripts/` | 制作・検証・比較・梱包のスクリプト |
| `SHA256SUMS.txt` | 全ファイルの SHA256 |

非公開の見比べ用: `TM_HM57_MATCH_PLAYER_20261111_RESEARCH_COMPARISON_NOT_FOR_RELEASE.zip`（参照モデルとの並び。公開不可）。

## 比較画像

| 画像 | 内容 |
|---|---|
| `S01_fullbody` / `S02_face` / `S03_neck_shoulder` / `S04_legs_boots` | 全身・顔・首肩・脚（静止） |
| `S05` / `S05b` | 首振り・ヘディング・スローインでの首と襟 |
| `S06` | 動作中の脇・膝裏 |
| `S07` | 5 動作の同じコマ |
| `S08` / `S09` | 試合中の距離（中継カメラ 25m）と、その画素の拡大 |
| `S10` | リプレイ（3.6m） |
| `S11` / `S11b` | スマホ画面（iPhone 横向きの解像度）での見え方 |
| `S12` | 選手の高さ 32〜96 画素での見え方 |

動画: `HM57_motion_full.mp4`（走る・蹴る・ヘディング・スローイン、3 列）、`HM57_closeups.mp4`（首振りの首・蹴りの膝・スローインの脇）、`HM57_match_replay.mp4`（試合カメラとスロー再生のリプレイ、HM57 と軽量版）、`HM57_browser_threejs_playback.mp4`（ブラウザでの連続再生）、`HM57_run.gif`。

## 作り直す手順

```
# 1. 生成 → 検証 → 動作検証 → 比較描画 → 動画 → iPhone 用シート
HM_BUILD=<出力フォルダ> HM56_BUILD=<HM56 の build> PY=python3.11 \
  [HM_RESEARCH_REF=<研究用参照の GLB（非公開の見比べだけ）>] bash scripts/run_all57.sh
# 2. ブラウザ（three.js）と glTF Validator
HM_BUILD=... THREE_DIR=<node_modules/three> PW_NODE_MODULES=<playwright のある node_modules> \
  VALIDATOR_NODE_MODULES=<gltf-validator のある node_modules> PY=python3.11 bash scripts/webtest57.sh
# 3. QA 表、ZIP と展開テスト
HM_BUILD=... python3.11 scripts/summarize57.py <HM56 の GLB> <HM57 の GLB> <HM57 軽量版の GLB>
HM_BUILD=... python3.11 scripts/package57.py
```

- 必要なもの: Python 3.11、bpy 4.2（PyPI）、numpy、scipy、Pillow、ffmpeg。ブラウザの確認には Node.js、three.js 0.186、Playwright、gltf-validator。
- `.blend` は Blender 4.2 で作成しました。**4.0.2 で開けるかは確認していません。**
