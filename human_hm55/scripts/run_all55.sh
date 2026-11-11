#!/usr/bin/env bash
# HM55 full pipeline (Blender part). Requires Python 3.11 + bpy==4.2.x (PyPI), numpy, scipy, Pillow.
# Usage: HM_BUILD=<new output dir> PY=<python> bash run_all55.sh
# Optional (comparison / audit only, never build input): FH53_INPUTS, FH53_REF04, FH54_BUILD.
# The node part (three.js browser test + Khronos glTF Validator) runs afterwards with webtest55.sh.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; : "${HM_BUILD:?}"; PY="${PY:-python3}"; export HM_BUILD
mkdir -p "$HM_BUILD/logs"
step() { echo "== $STEP"; "$@" > "$HM_BUILD/logs/$STEP.log" 2>&1 || { echo "FAILED: $STEP (see logs/$STEP.log)"; exit 1; }; }
STEP=00_build_all   step "$PY" -I "$HERE/build_all.py"
STEP=01_verify      step "$PY" -I "$HERE/verify_hm55.py"
STEP=02_renders     step "$PY" -I "$HERE/render_hm55.py"
STEP=03_sheets      step "$PY" -I "$HERE/compose_hm55.py"
if [ -n "${FH53_INPUTS:-}" ] && [ -n "${FH53_REF04:-}" ] && [ -n "${FH54_BUILD:-}" ]; then
  STEP=04_provenance step "$PY" -I "$HERE/provenance_audit.py"
else
  echo "== 04_provenance skipped (research inputs not provided)"
fi
echo "== done: $HM_BUILD"
