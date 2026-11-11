#!/usr/bin/env bash
# HM56 pipeline for the representative player (P0 x H2). Requires Python 3.11 + bpy 4.2 (PyPI), numpy, scipy, Pillow, ffmpeg.
# Usage: HM_BUILD=<new output dir> HM55_BUILD=<HM55 build folder with models/players> PY=<python> bash run_all56.sh
# HM55 is only read (its exported GLB is the "before" of every comparison). The 16-pattern rollout is NOT run here.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; : "${HM_BUILD:?}" "${HM55_BUILD:?}"; PY="${PY:-python3}"; export HM_BUILD
mkdir -p "$HM_BUILD/logs" "$HM_BUILD/qa"
OLD="$HM55_BUILD/models/players/TM_HM55_PLAYER_P0_H2_KITA.glb"; NEW="$HM_BUILD/models/players/TM_HM56_PLAYER_P0_H2_KITA.glb"
step() { echo "== $STEP"; "$@" > "$HM_BUILD/logs/$STEP.log" 2>&1 || { echo "FAILED: $STEP (see logs/$STEP.log)"; exit 1; }; }
STEP=00_build         step "$PY" -I "$HERE/build_all.py" --faces P0 --hairs H2 --quick
STEP=01_verify        step "$PY" -I "$HERE/verify_hm55.py" TM_HM56_PLAYER_P0_H2_KITA.glb
STEP=02_verify_motion step "$PY" -I "$HERE/verify_motion56.py" "$HM_BUILD/qa/verify_motion56.json" "$OLD" "$NEW"
STEP=03_compare       step "$PY" -I "$HERE/compare56.py" "$OLD" "$NEW"
STEP=04_video         step "$PY" -I "$HERE/anim_video56.py" "$OLD" "$NEW"
STEP=05_sheets        step "$PY" -I "$HERE/compose56.py"
echo "== done: $HM_BUILD"
