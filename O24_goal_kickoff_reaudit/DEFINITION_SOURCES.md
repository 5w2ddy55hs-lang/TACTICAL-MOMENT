# 確認した集計コード（O24）

どれも過去の各版のパック（このリポジトリ）にあるファイルです。変更していません。

| 版 | ファイル | 指標 | 型 |
|---|---|---|---|
| I17 監査（共通） | `I17_independent_audit/tools/analyze.mjs` | turnovers、transitions（loserRegainTick、winnerShot10s、loserGoalSide、allPlay5s）、concEpisodes / jointPress の ownWin3s、passes | C（切り替え）、D（3秒） |
| I18 | `I18_flight_shape_research/tools/paired_pass_eval.mjs` | outcome、teamHasBallAtEnd（プレー外は null） | E |
| I18 | `I18_flight_shape_research/tools/flight_metrics.mjs` | lost5s、regain5s、shot10s | D |
| J19 | `J19_pressure_research/tools/paired_def_eval.mjs` | regain、regainedByRestart（最初の再開で停止） | A |
| K20 | `K20_possession_research/tools/paired_k20.mjs` | poss3、poss6（最初の再開で停止。`restart:<チーム>`）、free の回収 | A |
| K20 | `K20_possession_research/tools/compare_poss.py` | 固定場面の poss+3s、poss+6s、possEnd（`restart:<種類>:<チーム>`） | A |
| L21 | `L21_k20_followup_research/tools/paired_multi.mjs` | poss3、poss6、regain2s、regain6s、collected3s、wentDead | A |
| M22 | `M22_l21_yield_research/tools/paired_from_branch.mjs` | 同上（L21 の試合を主試合にする版） | A |
| M22 | `M22_l21_yield_research/tools/yield_probe.mjs` | 60場面の再実行の poss3、poss6（6秒通算。元の結果の再現確認だけに使用） | B |
| M22 | `M22_l21_yield_research/tools/yield_scan.mjs` | 譲りの結果（dead_ball は得点を含む） | — |
| N23 | `N23_k20_possession_verification/tools/k20_probe.mjs`、`pair_kinds.mjs` | poss3、poss6（6秒通算） | B |
