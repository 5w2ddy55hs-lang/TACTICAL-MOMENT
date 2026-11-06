# TACTICAL MOMENT 顔・髪 FH54（FH53 からの改善）

**研究候補です。** 正式採用・本番置換・権利確認は行っていません。詳細は [REPORT_JA.md](REPORT_JA.md)、実測値の表は `qa/QA_TABLES54.md` にあります。

## git に入れていないもの

- このリポジトリは公開（public）です。
- `.blend`・`.glb`・テクスチャ・画像・ZIP は `face_hair_fh54/build/` に置き、`.gitignore` で除外しています。由来が未確認の研究素材を含むためです。
- git に入っているのは、スクリプト・報告書・数値だけの QA 記録です。

## ZIP の中身

| パス | 内容 |
|---|---|
| `models/face/TM_FH54_F{1,2,3}_*` | 顔の完成形（形とテクスチャの両方を変更）。20組で使用。 |
| `models/face/TM_FH54_F{n}S_*` | 形だけ変えた比較用 |
| `models/face/TM_FH54_F{n}T_*` | テクスチャだけ変えた比較用 |
| `models/hair/TM_FH54_H{1..4}_*` | 髪（Cap 不透明 + CapEdge 半透明 + Cards 半透明の構成） |
| `models/combos/TM_FH54_F?_H?.glb` | 顔4 × 髪5 = 20組（F0／H0 は FACE52 原本） |
| `models/TM_FH54_LIBRARY_faces_hairs.blend` | 全部品を集めた編集用ファイル |
| `models/review/TM_FH54_REVIEW_REF04_*.blend` | Reference04 への仮配置（静止）と、首の仮接続（固定／ウェイト転写） |
| `textures/` | 髪のテクスチャ（スクリプトで生成）と、顔ごとのテクスチャ（FACE52 由来を加工） |
| `images/` | 比較画像（M = スマホ向けの縦長、D = PC 向け） |
| `renders/` | 元のレンダー画像 |
| `webtest/` | ブラウザ（three.js）での検査の元画像と結果 |
| `qa/` | 検査の記録 |
| `logs/` | 実行ログ |
| `scripts/` | 制作・検査のスクリプト |
| `SHA256SUMS.txt` | 全ファイルの SHA256 |

## 開き方

- **.blend:** テクスチャはすべてファイルに格納済みです。作成・保存は Blender 4.2.23 LTS で、**4.0.2 で開けるかは確認していません**。
- **.glb:** FACE52 と同じ頭部ローカル座標です。Reference04 には (0, −0.0393776, 1.5979694) へ平行移動するだけで、回転・拡大はありません。
