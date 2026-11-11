# TACTICAL MOMENT 顔・髪 候補 FH53（2026-11-06）

**研究候補です。** 正式採用・本番モデルへの置換・権利確認は、いずれも行っていません。
制作の詳細・検査結果・残った課題は [REPORT_JA.md](REPORT_JA.md) にまとめています。

## このフォルダの扱い（git に含めないもの）

- このリポジトリは **公開（public）** です。
- FACE52 の顔テクスチャと Reference04 は『サカつく2002』由来の研究資料を含みます。そのため、`.blend`・`.glb`・テクスチャ・レンダー画像・ZIP は **git に入れていません**（`.gitignore` で `face_hair_fh53/build/` を除外）。
- git に入っているのは、私が書いたスクリプト、報告書、数値だけの QA 記録です。
- 実データ一式は ZIP（`TM_FH53_FACE_HAIR_CANDIDATES_20261106.zip`）で別途お渡しします。

## ZIP の中身

| パス | 内容 |
|---|---|
| `models/face/TM_FH53_F{1,2,3}_*.blend/.glb` | 顔候補（`REF09_Face_Eyes_Mouth` と、FACE52 から無変更の `REF14_BackScalp`）。F0 は FACE52 原本です。 |
| `models/hair/TM_FH53_H{1..4}_*.blend/.glb` | 髪候補（`REF09_Hair` を置き換えるモジュール）。H0 は FACE52 原本です。 |
| `models/combos/TM_FH53_F?_H?.glb` | 顔4 × 髪5 = 20 通りの頭部 GLB。すべて書き出し後に再読込して検査済みです。 |
| `models/TM_FH53_LIBRARY_faces_hairs.blend` | 全モジュールを集めた編集用ファイル（`FACE_*` と `HAIR_*` のコレクションを1つずつ表示して使います）。 |
| `models/review/TM_FH53_REVIEW_REF04_PROVISIONAL.blend` | Reference04 の体に仮置きしたレビュー用シーン。**接合・ウェイト・動作は未実施**です。 |
| `textures/TMH53_*.png` | 新しい髪のテクスチャ。`make_hair_textures.py` で生成したもので、既存画像は使っていません。 |
| `images/*.jpg` | 比較用のシート画像 |
| `renders/**.png` | レンダーの元画像（各画像とモデルの SHA の対応は `qa/render_ledger.json`） |
| `qa/` | 検査結果（JSON と `QA_TABLES.md`） |
| `logs/` | 全工程の実行ログ |
| `scripts/` | 制作・書き出し・検査・レンダーのスクリプト一式（`run_all.sh` で全工程を再実行できます） |
| `SHA256SUMS.txt` | ZIP 内の全ファイルの SHA256 |
| `INPUT_SHA256.txt` | 使った入力の SHA256 |

## 開き方

- **.blend:** そのまま開けます。テクスチャはすべてファイル内に格納しているので、外部ファイルは要りません。
  - 作成・保存は **Blender 4.2.23 LTS**（PyPI の bpy）で行いました。
  - **Blender 4.0.2 で開けるかは確認していません**。古い版で新しい版のファイルを開くことになるため、開けない場合は 4.2 LTS 以降を使ってください。
- **.glb:** glTF 2.0 です。座標系は FACE52 と同じ頭部ローカル座標で、ノードの移動・回転・拡大はありません。
  - Reference04 に置くときの移動量は Blender 座標で (0, −0.0393776, 1.5979694)、回転 0、倍率 1 です。

## 名前の付け方

- **顔:** `F0_FACE52`（原本）／`F1_LONG_ANGULAR`／`F2_ROUND_SOFT`／`F3_NARROW_SHARP`
- **髪:** `H0_FACE52`（原本）／`H1_STANDARD_REBUILT`／`H2_SHORT_CROP`／`H3_SWEPT_BACK`／`H4_SIDE_SWEPT_FRINGE`
- **組み合わせ:** `TM_FH53_F{n}_H{m}.glb`
