#!/usr/bin/env bash
# HM57 pipeline for the representative player (P0 x H1 x kit A) and its mobile LITE version.
# Requires Python 3.11 + bpy 4.2 (PyPI), numpy, scipy, Pillow, ffmpeg.
# Usage: HM_BUILD=<new output dir> HM56_BUILD=<HM56 build folder with models/players> PY=<python> \
#        [HM_RESEARCH_REF=<research reference GLB, private side-by-side only>] bash run_all57.sh
# HM56 is only read (its exported GLB is the "before" of every comparison). The 16-pattern rollout is NOT run here.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; : "${HM_BUILD:?}" "${HM56_BUILD:?}"; PY="${PY:-python3}"; export HM_BUILD
mkdir -p "$HM_BUILD/logs" "$HM_BUILD/qa"
OLD="$HM56_BUILD/models/players/TM_HM56_PLAYER_P0_H2_KITA.glb"; NEW="$HM_BUILD/models/players/TM_HM57_PLAYER_P0_H1_KITA.glb"; LITE="$HM_BUILD/models/players/TM_HM57_PLAYER_P0_H1_KITA_LITE.glb"
REF=(); [ -n "${HM_RESEARCH_REF:-}" ] && REF=(--ref "$HM_RESEARCH_REF")
step() { echo "== $STEP"; "$@" > "$HM_BUILD/logs/$STEP.log" 2>&1 || { echo "FAILED: $STEP (see logs/$STEP.log)"; exit 1; }; }
STEP=00_build         step bash -c '"$0" -I "$1/build_all.py" --faces P0 --hairs H1 --quick || { echo "retry after a crash"; "$0" -I "$1/build_all.py" --faces P0 --hairs H1 --quick; }' "$PY" "$HERE"
# bpy 4.2 (PyPI) has crashed intermittently in these steps (memory corruption around mesh decimation): each build step is retried once.
# LITE runs in its own process.
STEP=00b_lite         step bash -c '"$0" -I "$1/build_all.py" --faces P0 --hairs H1 --quick --lite-only || { echo "retry after a crash"; "$0" -I "$1/build_all.py" --faces P0 --hairs H1 --quick --lite-only; }' "$PY" "$HERE"
STEP=01_verify        step "$PY" -I "$HERE/verify_hm55.py" TM_HM57_PLAYER_P0_H1_KITA.glb
STEP=02_verify_motion step "$PY" -I "$HERE/verify_motion57.py" "$HM_BUILD/qa/verify_motion57.json" "$OLD" "$NEW" "$LITE"
STEP=03_compare       step "$PY" -I "$HERE/compare57.py" HM56="$OLD" HM57="$NEW" HM57L="$LITE" "${REF[@]}"
STEP=04_video         step "$PY" -I "$HERE/anim_video57.py" "$OLD" "$NEW" "$LITE"
STEP=05_sheets        step "$PY" -I "$HERE/compose57.py"
echo "== done: $HM_BUILD"
