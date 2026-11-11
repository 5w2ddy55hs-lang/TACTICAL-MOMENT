# TACTICAL MOMENT 人間モデル HM56（HM55 の改善候補）

**候補です。** 正式採用・公開はしていません。詳細は [REPORT_JA.md](REPORT_JA.md)、実測値の表は `qa/QA_TABLES56.md` にあります。

- HM56 は、HM55 の生成スクリプトを `human_hm56/scripts/` に複製して編集し、作り直した選手モデルです。
- **HM55 の原本・生成スクリプト・検証結果（`human_hm55/`）は変更していません。** HM55 の GLB は、比較の「改良前」として読むだけです。
- 今回作ったのは **代表の 1 体（顔 P0 × 髪 H2 × ユニフォーム A）だけ** です。16 パターンへの展開はしていません。品質を確認していただいてから行います。
- 骨・動作 6 本は HM55 と同じです（GLB のバイナリを比較して一致を確認）。ウェイトは、新しい体形に合わせて同じ規則で作り直しています。
- 試合 AI には触れていません。外部サービスへのアップロード、購入、API クレジットの使用はしていません。
- 研究用の参照モデル（Reference04・FACE52・FH54）は、生成にも比較画像にも使っていません。比較画像に写っているのは HM55 と HM56 だけです。

## git に入れていないもの

- このリポジトリは公開（public）です。
- `.blend`・`.glb`・テクスチャ・画像・動画・ZIP は `human_hm56/build/` に置き、`.gitignore` で除外しています。
- git に入っているのは、スクリプト・報告書・数値だけの QA 記録（`qa/`）です。

## ZIP の中身（`TM_HM56_HUMAN_MODEL_20261111.zip`）

| パス | 内容 |
|---|---|
| `models/players/TM_HM56_PLAYER_P0_H2_KITA.glb` | 改善した代表の選手（骨 22 本・ウェイト・動作 6 本入り） |
| `models/players/TM_HM56_PLAYER_P0_H2_KITA.blend` | 同じ選手の編集用ファイル（テクスチャ格納済み） |
| `models/TM_HM56_LIBRARY.blend` | 骨・胴体・頭・髪・動作をまとめた編集用の原本 |
| `models/modules/` | 部品ごとの GLB（胴体・頭・髪）。どれも同じ骨組みに付いています |
| `textures/` | 生成したテクスチャ（顔・腕脚の肌・ユニフォーム・髪） |
| `images/C01〜C09_*.jpg` | **iPhone 向けの比較画像**（幅 1080px、縦に並べた改良前 → 改良後） |
| `renders/COMPARE/` | 比較画像の元の描画（HM55 と HM56 を同じカメラ・姿勢・照明で 1 枚ずつ） |
| `video/` | 連続再生の動画（MP4 は iPhone で再生できる H.264 形式）と GIF |
| `webtest/` | ブラウザ（three.js）で再生したときの画像と結果 |
| `qa/`、`logs/` | 検証の記録、実行ログ |
| `scripts/` | 制作・検証・比較・梱包のスクリプト |
| `SHA256SUMS.txt` | 全ファイルの SHA256 |

## 比較画像（iPhone で縦にスクロールして見る想定）

| 画像 | 内容 |
|---|---|
| `C01_fullbody_before_after` | 全身：正面・横・斜め・背面 |
| `C02_face_before_after` | 顔：正面・斜め・横・下から |
| `C03_neck_shoulder_before_after` | 首から肩・胸・背中へのつながり |
| `C04_legs_boots_before_after` | 膝・ふくらはぎ・足首・スパイク |
| `C05_neck_in_motion`、`C05b_neck_in_motion_back` | 首振り・見上げ・ヘディングなどの姿勢での首と襟 |
| `C06_armpit_knee_in_motion` | 動作中の脇とシャツ、膝裏とソックス |
| `C07_motion_frames` | 走る・蹴る・ヘディング・スローインの複数コマ |
| `C08_match_distance`、`C09_match_distance_zoom` | 試合中の距離（中継カメラ）と、小さい表示（48・72・96px） |

動画: `HM55_vs_HM56_motion_full.mp4`（全身、左右並び）、`HM55_vs_HM56_neck_knee_closeup.mp4`（首と膝の拡大）、`HM55_vs_HM56_run.gif`、`HM56_browser_threejs_playback.mp4`（ブラウザでの連続再生）。

## 開き方

- **.blend:** テクスチャは格納済みです。作成は Blender 4.2 LTS（PyPI の bpy 4.2）で、**4.0.2 で開けるかは確認していません**。
- **.glb:** 単位はメートル、足元が原点、正面は glTF の +Z 方向です。骨は 22 本、動作は `TM_HM55_Idle / Run / Kick / LookAround / ThrowIn / Header` の 6 本です（骨と動作を HM55 と同一にするため、骨組みと動作の名前は HM55 のままです）。

## 作り直す手順

```
# 1. 代表 1 体の生成 → 検証 → 動作検証 → 比較描画 → 動画 → iPhone 用シート
HM_BUILD=<新しい出力フォルダ> HM55_BUILD=<HM55 の build フォルダ> PY=python3.11 bash scripts/run_all56.sh
# 2. ブラウザでの連続再生と glTF Validator（任意。three.js・Playwright・gltf-validator が必要）
HM_BUILD=... THREE_DIR=<node_modules/three> PW_NODE_MODULES=<playwright のある node_modules> \
  VALIDATOR_NODE_MODULES=<gltf-validator のある node_modules> PY=python3.11 bash scripts/webtest56.sh
# 3. QA 表、ZIP と展開テスト
HM_BUILD=... python3.11 scripts/summarize56.py <HM55 の GLB> <HM56 の GLB>
HM_BUILD=... python3.11 scripts/package56.py
```

- 必要なもの: Python 3.11、bpy 4.2、numpy、scipy、Pillow、ffmpeg
- 「改良前」には HM55 の `models/players/TM_HM55_PLAYER_P0_H2_KITA.glb` を使います（`human_hm55/scripts/run_all55.sh` で作り直せます）。
