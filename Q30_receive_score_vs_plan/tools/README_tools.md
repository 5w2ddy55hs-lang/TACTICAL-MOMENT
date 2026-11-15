# Q30 tools
- plan_vs_choice.mjs: scan base recordings for decisions where the engine's own reception gate yields a plan but receive/intercept was not chosen.
- followup_episodes.py: group rows into episodes, classify (possession penalty vs distance/ahead-friends), check whether a plan was present at the next receive decision.
- plan_episode_trace.mjs: per-player trace with score decomposition, plan metrics, hypothetical plan-target-distance score (analysis only) and truth.
- eval/episodes_summary.txt was produced by an inline script (grouping + candidate listing); eval/hypothetical_flip_stats.txt by an inline script replacing the distance term with the plan-target distance on the 221 rows. Both read eval/plan_vs_choice.json only.
