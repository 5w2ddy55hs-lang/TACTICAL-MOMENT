# HM55 QA 表（スクリプト出力の実測値）

## 1. 構成（書き出した GLB の実測）

| GLB | 三角形 | 属性頂点 | プリミティブ | 画像 | 骨 | 動作 |
|---|---|---|---|---|---|---|
| TM_HM55_PLAYER_P0_H1_KITA.glb | 6678 | 4147 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P0_H1_KITB.glb | 6678 | 4147 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P0_H2_KITA.glb | 6478 | 3905 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P0_H3_KITA.glb | 6754 | 4176 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P0_H4_KITA.glb | 6770 | 4272 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P1_H1_KITA.glb | 6678 | 4147 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P1_H2_KITA.glb | 6478 | 3905 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P1_H2_KITB.glb | 6478 | 3905 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P1_H3_KITA.glb | 6754 | 4176 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P1_H4_KITA.glb | 6770 | 4272 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P2_H1_KITA.glb | 6678 | 4147 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P2_H2_KITA.glb | 6478 | 3905 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P2_H3_KITA.glb | 6754 | 4176 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P2_H3_KITB.glb | 6754 | 4176 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P2_H4_KITA.glb | 6770 | 4272 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P3_H1_KITA.glb | 6678 | 4147 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P3_H2_KITA.glb | 6478 | 3905 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P3_H3_KITA.glb | 6754 | 4176 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P3_H4_KITA.glb | 6770 | 4272 | 6 | 6 | 22 | 6 |
| TM_HM55_PLAYER_P3_H4_KITB.glb | 6770 | 4272 | 6 | 6 | 22 | 6 |

### 材質（代表 1 体）

| 材質 | alphaMode | 両面 |
|---|---|---|
| TM_HM55_Kit_A | OPAQUE | True |
| TM_HM55_BodySkin_T2 | OPAQUE | False |
| TMH55_H1_Cap | OPAQUE | True |
| TMH55_H1_CapEdge | BLEND | True |
| TMH55_H1_Cards | BLEND | True |
| TM_HM55_Head_P0 | OPAQUE | False |

### 動作クリップ

| 名前 | 秒 | キー数 |
|---|---|---|
| TM_HM55_Header | 1.4 | 43 |
| TM_HM55_Idle | 2 | 61 |
| TM_HM55_Kick | 1.333 | 41 |
| TM_HM55_LookAround | 3.333 | 101 |
| TM_HM55_Run | 0.667 | 21 |
| TM_HM55_ThrowIn | 1.5 | 46 |

### モジュール別の三角形数（生成時）

| 部品 | 三角形 | 頂点 |
|---|---|---|
| 胴体（ユニフォーム＋腕脚の肌） | 2552 | 1402 |
| 頭 P0 NEUTRAL（顔・首・耳） | 1988 | 1029 |
| 頭 P1 LONG_ANGULAR（顔・首・耳） | 1988 | 1029 |
| 頭 P2 ROUND_SOFT（顔・首・耳） | 1988 | 1029 |
| 頭 P3 NARROW_SHARP（顔・首・耳） | 1988 | 1029 |
| 髪 H1_STANDARD（P0 用） | 2138（cap 1890、うち縁の帯 560、毛束 248） | 1291 |
| 髪 H2_SHORT_CROP（P0 用） | 1938（cap 1890、うち縁の帯 560、毛束 48） | 1053 |
| 髪 H3_SWEPT_BACK（P0 用） | 2214（cap 1944、うち縁の帯 576、毛束 270） | 1327 |
| 髪 H4_SIDE_SWEPT_FRINGE（P0 用） | 2230（cap 1890、うち縁の帯 560、毛束 340） | 1385 |

## 2. 首と襟（優先①）：全動作・全コマの実測

測定: 書き出した GLB を読み直し、各コマで姿勢を付けた頂点から計算。襟の隙間 = 襟の輪の各頂点から首の表面までの最短距離。首×シャツ = 頭部メッシュと上半身のシャツの三角形交差の対の数。見通し = 襟の隙間の中央を斜め上 3 方向から通した光線が、9cm 以内で肌に当たらなかった本数。

| 選手 | 動作 | コマ | 胸に対する頭の回転 最大° | 襟の隙間 最小〜最大 mm | 首×シャツ 交差 最大 | 見通し 失敗/本数 |
|---|---|---|---|---|---|---|
| P0_H2 | 静止 | — | 0 | 11.32〜15.77 | 0 | 0/27 |
| P0_H2 | Idle | 0〜60 | 3.6 | 11.32〜15.84 | 0 | 0/27 |
| P0_H2 | Run | 0〜20 | 10.7 | 11.35〜16.29 | 0 | 0/27 |
| P0_H2 | Kick | 0〜40 | 24.9 | 10.75〜16.36 | 0 | 0/27 |
| P0_H2 | LookAround | 0〜100 | 66.1 | 10.14〜20.52 | 0 | 0/27 |
| P0_H2 | ThrowIn | 0〜45 | 8.9 | 11.24〜15.85 | 0 | 0/27 |
| P0_H2 | Header | 0〜42 | 44.9 | 10.26〜16.84 | 0 | 0/27 |
| P1_H2 | 静止 | — | 0 | 11.32〜15.77 | 0 | 0/27 |
| P1_H2 | Idle | 0〜60 | 3.6 | 11.32〜15.84 | 0 | 0/27 |
| P1_H2 | Run | 0〜20 | 10.7 | 11.35〜16.29 | 0 | 0/27 |
| P1_H2 | Kick | 0〜40 | 24.9 | 10.75〜16.36 | 0 | 0/27 |
| P1_H2 | LookAround | 0〜100 | 66.1 | 10.14〜20.52 | 0 | 0/27 |
| P1_H2 | ThrowIn | 0〜45 | 8.9 | 11.24〜15.85 | 0 | 0/27 |
| P1_H2 | Header | 0〜42 | 44.9 | 10.26〜16.84 | 0 | 2/27 |
| P2_H2 | 静止 | — | 0 | 11.32〜15.77 | 0 | 0/27 |
| P2_H2 | Idle | 0〜60 | 3.6 | 11.32〜15.84 | 0 | 0/27 |
| P2_H2 | Run | 0〜20 | 10.7 | 11.35〜16.29 | 0 | 0/27 |
| P2_H2 | Kick | 0〜40 | 24.9 | 10.75〜16.36 | 0 | 0/27 |
| P2_H2 | LookAround | 0〜100 | 66.1 | 10.14〜20.52 | 0 | 0/27 |
| P2_H2 | ThrowIn | 0〜45 | 8.9 | 11.24〜15.85 | 0 | 0/27 |
| P2_H2 | Header | 0〜42 | 44.9 | 10.26〜16.84 | 0 | 0/27 |
| P3_H2 | 静止 | — | 0 | 11.32〜15.77 | 0 | 0/27 |
| P3_H2 | Idle | 0〜60 | 3.6 | 11.32〜15.84 | 0 | 0/27 |
| P3_H2 | Run | 0〜20 | 10.7 | 11.35〜16.29 | 0 | 0/27 |
| P3_H2 | Kick | 0〜40 | 24.9 | 10.75〜16.36 | 0 | 0/27 |
| P3_H2 | LookAround | 0〜100 | 66.1 | 10.14〜20.52 | 0 | 0/27 |
| P3_H2 | ThrowIn | 0〜45 | 8.9 | 11.24〜15.85 | 0 | 0/27 |
| P3_H2 | Header | 0〜42 | 44.9 | 10.26〜16.84 | 0 | 2/27 |

### スキンの伸縮と、肌と布の交差（代表 1 体）

辺の伸縮 = 姿勢を付けた辺の長さ ÷ 静止時の長さ。肌×布 = 肌の三角形とユニフォームの三角形の交差の対の数（静止時は 0）。

| 動作 | 胴体の辺 最大 / 上位1% | 頭部の辺 最小 / 下位1% / 上位1% / 最大 | 肌×布 最大（コマ） | 最大コマでの内訳 |
|---|---|---|---|---|
| Idle | 1.13 / 1.06 | 0.95 / 0.97 / 1.03 / 1.06 | 10（0） | {'arm x shirt': 10} |
| Run | 2.1 / 1.36 | 0.81 / 0.89 / 1.23 / 1.44 | 39（14） | {'arm x shirt': 11, 'knee_thigh x sock': 26, 'shorts x sock': 2} |
| Kick | 3.66 / 1.34 | 0.48 / 0.8 / 1.21 / 1.41 | 29（13） | {'knee_thigh x sock': 27, 'shorts x sock': 2} |
| LookAround | 1.13 / 1.07 | 0.47 / 0.64 / 1.89 / 2.55 | 10（0） | {'arm x shirt': 10} |
| ThrowIn | 1.52 / 1.23 | 0.81 / 0.91 / 1.17 / 1.33 | 13（36） | {'arm x shirt': 13} |
| Header | 2.43 / 1.45 | 0.47 / 0.67 / 1.42 / 1.75 | 26（8） | {'knee_thigh x sock': 26} |

| メッシュ | 頂点 | ウェイト合計 最小〜最大 | 1頂点あたりの骨 最大 |
|---|---|---|---|
| TM_HM55_Body | 1586 | 1.0〜1.0 | 2 |
| TM_HM55_Hair | 1207 | 1.0〜1.0 | 1 |
| TM_HM55_Head | 1112 | 1.0〜1.0 | 3 |

## 3. 肌色（優先②）：最終テクスチャの平均色

頭部モジュールに首が含まれるため、頭と胴体のあいだに肌どうしの継ぎ目はありません。下は離れた部位どうしの色の差です（sRGB 0〜1、ΔE は CIE76）。

| 顔 | 肌の色調 | 首 | 頬 | 前腕 | 膝 | ΔE 首−頬 | ΔE 首−前腕 | ΔE 首−膝 | 首の後ろの UV 継ぎ目の色差 |
|---|---|---|---|---|---|---|---|---|---|
| P0 | T2 | [0.7805, 0.5994, 0.4676] | [0.7848, 0.5904, 0.4597] | [0.7702, 0.5912, 0.4612] | [0.7425, 0.5657, 0.4408] | 1.63 | 0.86 | 3.39 | 0.0031 |
| P1 | T3 | [0.6891, 0.5106, 0.386] | [0.6411, 0.4738, 0.3632] | [0.6884, 0.5095, 0.3843] | [0.6636, 0.4875, 0.3673] | 4.39 | 0.15 | 2.35 | 0.0026 |
| P2 | T1 | [0.8399, 0.6692, 0.5429] | [0.8448, 0.6424, 0.5188] | [0.8328, 0.6633, 0.538] | [0.8028, 0.6347, 0.5142] | 3.98 | 0.6 | 3.33 | 0.0033 |
| P3 | T2 | [0.782, 0.6006, 0.4686] | [0.7845, 0.5945, 0.4634] | [0.7702, 0.5912, 0.4612] | [0.7425, 0.5657, 0.4408] | 1.05 | 0.99 | 3.51 | 0.0031 |

陰影を焼き込む前の塗りの平均色（同じ色定義から作っていることの確認）:

| 対象 | 平均 sRGB |
|---|---|
| body_T1 | [0.8589, 0.6818, 0.5531] |
| body_T2 | [0.7943, 0.6077, 0.4741] |
| body_T3 | [0.7099, 0.5237, 0.3951] |
| head_P0 | [0.8003, 0.6152, 0.4802] |
| head_P1 | [0.708, 0.5252, 0.3971] |
| head_P2 | [0.8648, 0.6898, 0.5598] |
| head_P3 | [0.8002, 0.6151, 0.4801] |

## 4. 髪と耳（優先③）：16 組の実測

縁の高さ = 頭皮層（cap＋生え際の帯）の外周の頂点が、頭の表面（耳を除く）から浮いている高さ。耳の近く = 方位 58〜102°。

| 組 | 髪の三角形 | 髪×頭 交差 | 縁の頂点 | 縁の高さ 最小/中央/最大 mm | 耳の近くの縁 中央/最大 mm | 髪と耳の最短距離 mm |
|---|---|---|---|---|---|---|
| P0_H1 | 2138 | 0 | 71 | 0.69/1.25/2.59 | 1.11/1.44 | 4.76 |
| P0_H2 | 1938 | 0 | 71 | 0.6/1.09/2.5 | 1.07/1.37 | 7.31 |
| P0_H3 | 2214 | 0 | 73 | 0.81/1.35/2.76 | 1.24/1.54 | 10.06 |
| P0_H4 | 2230 | 0 | 71 | 0.79/1.36/2.73 | 1.22/1.51 | 4.85 |
| P1_H1 | 2138 | 0 | 71 | 0.76/1.25/2.89 | 1.1/1.41 | 5.93 |
| P1_H2 | 1938 | 0 | 71 | 0.69/1.08/2.79 | 1.06/1.32 | 8.96 |
| P1_H3 | 2214 | 0 | 73 | 0.88/1.37/2.99 | 1.22/1.5 | 11.61 |
| P1_H4 | 2230 | 0 | 71 | 0.84/1.35/2.99 | 1.19/1.5 | 6.0 |
| P2_H1 | 2138 | 0 | 71 | 0.66/1.21/2.35 | 1.15/1.44 | 3.32 |
| P2_H2 | 1938 | 0 | 71 | 0.38/1.09/2.25 | 1.08/1.41 | 5.29 |
| P2_H3 | 2214 | 0 | 73 | 0.82/1.35/2.47 | 1.27/1.55 | 6.21 |
| P2_H4 | 2230 | 0 | 71 | 0.77/1.33/2.45 | 1.25/1.52 | 3.47 |
| P3_H1 | 2138 | 0 | 71 | 0.69/1.26/2.88 | 1.09/1.47 | 6.58 |
| P3_H2 | 1938 | 0 | 71 | 0.61/1.08/2.79 | 1.01/1.37 | 8.69 |
| P3_H3 | 2214 | 0 | 73 | 0.82/1.38/3.05 | 1.21/1.55 | 10.54 |
| P3_H4 | 2230 | 0 | 71 | 0.77/1.36/3.04 | 1.18/1.57 | 6.69 |

## 5. 出自の監査

- FACE52 の顔の頂点 516 個のうち、引継ぎ資料の平行移動を掛けると Reference04 の頂点と一致するもの: **326 個**

| 以前の成果物 | FACE52 と同じ面構成 | FACE52 と同じ UV | 動かしていない頂点 | テクスチャと FACE52 の相関（最大） |
|---|---|---|---|---|
| TM_FH54_F1_LONG_ANGULAR | True | True | 169 / 516 | 1.0 |
| TM_FH54_F2_ROUND_SOFT | True | True | 195 / 516 | 1.0 |
| TM_FH54_F3_NARROW_SHARP | True | True | 201 / 516 | 1.0 |

| HM55 のメッシュ | 頂点 | 三角形 | 研究用メッシュと同じ頂点数・三角形数 | 一致する頂点（Reference04 / FACE52 / FH54 の最大） |
|---|---|---|---|---|
| TM_HM55_Body | 1383 | 2552 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P0_H1 | 1291 | 2138 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P0_H2 | 1053 | 1938 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P0_H3 | 1327 | 2214 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P0_H4 | 1385 | 2230 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P1_H1 | 1291 | 2138 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P1_H2 | 1053 | 1938 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P1_H3 | 1327 | 2214 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P1_H4 | 1385 | 2230 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P2_H1 | 1291 | 2138 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P2_H2 | 1053 | 1938 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P2_H3 | 1327 | 2214 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P2_H4 | 1385 | 2230 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P3_H1 | 1291 | 2138 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P3_H2 | 1053 | 1938 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P3_H3 | 1327 | 2214 | False | 0 / 0 / 0 |
| TM_HM55_Hair_P3_H4 | 1385 | 2230 | False | 0 / 0 / 0 |
| TM_HM55_Head_P0 | 1029 | 1988 | False | 0 / 0 / 0 |
| TM_HM55_Head_P1 | 1029 | 1988 | False | 0 / 0 / 0 |
| TM_HM55_Head_P2 | 1029 | 1988 | False | 0 / 0 / 0 |
| TM_HM55_Head_P3 | 1029 | 1988 | False | 0 / 0 / 0 |

| HM55 のテクスチャ | 大きさ | 最も似た研究用画像 | 相関 |
|---|---|---|---|
| TM_HM55_BodySkin_T1 | 512x512 | FH54/TMF54_F1_FACE.png | 0.552 |
| TM_HM55_BodySkin_T2 | 512x512 | FH54/TMF54_F1_FACE.png | 0.596 |
| TM_HM55_BodySkin_T2.001 | 512x512 | FH54/TMF54_F1_FACE.png | 0.596 |
| TM_HM55_BodySkin_T2.002 | 512x512 | FH54/TMF54_F1_FACE.png | 0.596 |
| TM_HM55_BodySkin_T3 | 512x512 | FH54/TMF54_F1_FACE.png | 0.632 |
| TM_HM55_Head_P0 | 1024x1024 | FH54/TMF54_F1_NECK.png | 0.674 |
| TM_HM55_Head_P1 | 1024x1024 | FH54/TMF54_F1_NECK.png | 0.683 |
| TM_HM55_Head_P2 | 1024x1024 | FH54/TMF54_F1_NECK.png | 0.655 |
| TM_HM55_Head_P3 | 1024x1024 | FH54/TMF54_F1_NECK.png | 0.676 |
| TM_HM55_Kit_A | 1024x1024 | Reference04/00_X01ASI.png | -0.487 |
| TM_HM55_Kit_A.001 | 1024x1024 | Reference04/00_X01ASI.png | -0.487 |
| TM_HM55_Kit_A.002 | 1024x1024 | Reference04/00_X01ASI.png | -0.487 |
| TM_HM55_Kit_A.003 | 1024x1024 | Reference04/00_X01ASI.png | -0.487 |
| TM_HM55_Kit_A.004 | 1024x1024 | Reference04/00_X01ASI.png | -0.487 |
| TMH55_CAP_STRANDS_512 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.001 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.002 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.003 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.004 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.005 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.006 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.007 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.008 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.009 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.010 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.011 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.012 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.013 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.014 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CAP_STRANDS_512.015 | 512x512 | FH54/TMF54_F1_FACE.png | 0.139 |
| TMH55_CARD_STRANDS_512 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.001 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.002 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.003 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.004 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.005 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.006 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.007 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.008 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.009 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.010 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.011 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.012 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.013 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.014 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_CARD_STRANDS_512.015 | 512x512 | Reference04/00_X01ASI.png | -0.519 |
| TMH55_EDGE_STRANDS_512x256 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.001 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.002 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.003 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.004 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.005 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.006 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.007 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.008 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.009 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.010 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.011 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.012 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.013 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.014 | 512x256 | Reference04/00_X01ASI.png | -0.682 |
| TMH55_EDGE_STRANDS_512x256.015 | 512x256 | Reference04/00_X01ASI.png | -0.682 |

- 骨: HM55 22 本、Reference04 21 本。同じ名前の骨 0、関節位置が 1mm 以内で一致するもの 0。
- 動作: HM55 = ['TM_HM55_Header', 'TM_HM55_Idle', 'TM_HM55_Kick', 'TM_HM55_LookAround', 'TM_HM55_Run', 'TM_HM55_ThrowIn']、Reference04 = ['REF_gamemtn0_id0001_normalized_phase', 'REF_gamemtn0_id0039_normalized_phase', 'REF_gamemtn0_id1012_normalized_phase']
- 生成スクリプト内のファイル読み込み箇所: 3 か所（すべて同じビルドで書き出したテクスチャの読み戻しと SHA 計算。一覧は provenance_audit.json）

## 6. glTF Validator（Khronos 公式 2.0.0-dev.3.10）

- 対象 42 ファイル、エラー 0、警告 82、情報 0
  - W NODE_SKINNED_MESH_NON_ROOT /nodes/22 Node with a skinned mesh is not root. Parent transforms will not affect a skinned mesh.
  - W NODE_SKINNED_MESH_NON_ROOT /nodes/23 Node with a skinned mesh is not root. Parent transforms will not affect a skinned mesh.
  - W NODE_SKINNED_MESH_NON_ROOT /nodes/24 Node with a skinned mesh is not root. Parent transforms will not affect a skinned mesh.

## 7. ブラウザ（three.js 0.186.1、ヘッドレス Chromium + SwiftShader ソフトウェア描画）

| モデル | スキン付きメッシュ | 骨 | クリップ | 描画順を最悪にしたときの変化画素% [斜め, 上, 背面, 側面] | 裏面を描かない設定での変化画素% |
|---|---|---|---|---|---|
| TM_HM55_PLAYER_P0_H2_KITA | 6 | 22 | 6 | [0.0, 0.0, 0.0, 0.005] | 0.916 |
| TM_HM55_PLAYER_P1_H1_KITA | 6 | 22 | 6 | [0.039, 0.002, 0.0, 0.0] | 0.859 |
| TM_HM55_PLAYER_P2_H4_KITA | 6 | 22 | 6 | [0.0, 0.0, 0.0, 0.034] | 0.893 |
| TM_HM55_PLAYER_P3_H3_KITA | 6 | 22 | 6 | [0.0, 0.0, 0.0, 0.0] | 0.957 |

| 22 体表示 | 描画コール | 三角形 | ms/コマ（SwiftShader、参考値） |
|---|---|---|---|
| TM_HM55_PLAYER_P0_H2_KITA_x22_idle | 158 | 143462 | 5.08 |
| TM_HM55_PLAYER_P0_H2_KITA_x22_run | 158 | 143462 | 3.25 |

- ページのエラー: 0 件
