# TACTICAL MOMENT 人間モデル HM55（独自制作の候補）

**候補です。** 正式採用はしていません。詳細は [REPORT_JA.md](REPORT_JA.md)、実測値の表は `qa/QA_TABLES55.md` にあります。

- HM55 は、頭・胴体・髪・テクスチャ・骨・ウェイト・動作のすべてを、このフォルダのスクリプトだけで生成した選手モデルです。
- Reference04、FACE52、FH53、FH54 のメッシュ・画像・骨・動作は、生成の入力に使っていません。開くのは出自の監査と、見比べ用の描画だけです。
- 権利上の最終判断（公開・商用利用してよいか）は、利用者側の確認が必要です。ここでは出自の実測結果を示すところまでです。

## git に入れていないもの

- このリポジトリは公開（public）です。
- `.blend`・`.glb`・テクスチャ・画像・ZIP は `human_hm55/build/` に置き、`.gitignore` で除外しています。
- git に入っているのは、スクリプト・報告書・数値だけの QA 記録です。
- HM55 自体は独自制作ですが、公開するかどうかはまだ決めていただいていないため、モデルと画像は入れていません。

## ZIP の中身

| パス | 内容 |
|---|---|
| `models/players/TM_HM55_PLAYER_P?_H?_KIT?.glb` | 組み立て済みの選手（骨・ウェイト・動作 6 本入り）。顔 4 × 髪 4 の 16 体（ユニフォーム A）と、ユニフォーム B の 4 体 |
| `models/players/*.blend` | 代表の組み合わせの編集用ファイル |
| `models/modules/` | 部品ごとの GLB（胴体 2、頭 4、髪 16）。どれも同じ骨組みに付いています |
| `models/TM_HM55_LIBRARY.blend` | 骨・胴体・全部の頭と髪・動作をまとめた編集用ファイル |
| `textures/` | 生成したテクスチャ（顔 4、腕脚の肌 3 色、ユニフォーム 2、髪 3） |
| `images/` | 比較画像（M = スマホ向け、D = PC 向け） |
| `renders/` | 元の描画画像 |
| `review_research_comparison_NOT_FOR_RELEASE/` | 研究用の参照モデルが写っている比較画像。**公開物に入れないでください** |
| `webtest/` | ブラウザ（three.js）での確認画像と結果 |
| `qa/`、`logs/` | 検査の記録、実行ログ |
| `scripts/` | 制作・検査のスクリプト |
| `SHA256SUMS.txt` | 全ファイルの SHA256 |

## 名前の対応

| 記号 | 意味 |
|---|---|
| P0〜P3 | 顔（P0 基準、P1 面長、P2 丸顔、P3 細面）。首まで含みます |
| H1〜H4 | 髪（H1 標準、H2 短髪、H3 オールバック、H4 片流し） |
| KITA / KITB | ユニフォームの色違い |
| T1〜T3 | 肌の色調。顔ごとに決まっていて、腕と脚のテクスチャも同じ色調を使います |

## 開き方

- **.blend:** テクスチャは格納済みです。作成は Blender 4.2 LTS で、**4.0.2 で開けるかは確認していません**。
- **.glb:** 単位はメートル、足元が原点、正面は glTF の +Z 方向です。骨は 22 本、動作は `TM_HM55_Idle / Run / Kick / LookAround / ThrowIn / Header` の 6 本です。

## 作り直す手順

```
HM_BUILD=<新しい出力フォルダ> PY=python3.11 bash scripts/run_all55.sh
```

- 必要なもの: Python 3.11、bpy 4.2、numpy、scipy、Pillow
- 研究用の入力（`FH53_INPUTS`、`FH53_REF04`、`FH54_BUILD`）を指定すると、出自の監査と見比べ用の描画も行います。指定しなくてもモデルは作れます。
- ブラウザの確認と glTF Validator は `scripts/webtest55.sh`、ZIP は `scripts/package55.py` です。
