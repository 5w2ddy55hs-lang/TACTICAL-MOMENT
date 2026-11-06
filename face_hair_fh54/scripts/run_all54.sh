#!/usr/bin/env bash
# FH54 full pipeline (Blender part). Requires Python 3.11 + bpy==4.2.23 (PyPI), numpy, scipy, Pillow.
# Usage: FH53_INPUTS=<restored_inputs> FH53_REF04=<Reference04 dir> FH53_REFERENCE=<extracted FH53 ZIP folder>
#        FH53_BUILD=<new output dir> [FH54_PREFIX_BUILD=<pre-fix build>] PY=<python> bash run_all54.sh
# The node part (three.js browser test + Khronos glTF Validator) runs afterwards with webtest_all.sh; then re-run
# compose54.py (M10 needs build/webtest/force) and summarize54.py (§7, §8 need the webtest / validator JSON).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${FH53_INPUTS:?}" "${FH53_REF04:?}" "${FH53_BUILD:?}" "${FH53_REFERENCE:?}"; PY="${PY:-python3}"
export FH53_INPUTS FH53_REF04 FH53_BUILD FH53_REFERENCE
mkdir -p "$FH53_BUILD/logs"
step() { echo "== $STEP"; "$@" > "$FH53_BUILD/logs/$STEP.log" 2>&1 || { echo "FAILED: $STEP (see logs/$STEP.log)"; exit 1; }; }
STEP=00_hair_textures  step "$PY" -I "$HERE/make_hair_textures.py" "$FH53_BUILD/textures"
STEP=01_face_textures  step "$PY" -I "$HERE/face_textures54.py"
STEP=02_faces          step "$PY" -I "$HERE/build_faces54.py"
STEP=03_hairs          step "$PY" -I "$HERE/build_hairs.py"
STEP=04_combos         step "$PY" -I "$HERE/export_combos.py"
STEP=05_verify         step "$PY" -I "$HERE/verify_all.py"
STEP=06_face_qa        step "$PY" -I "$HERE/qa_faces54.py"
STEP=07_renders        step "$PY" -I "$HERE/render_final54.py"
STEP=08_face_distinct  step "$PY" -I "$HERE/face_distinct54.py"
STEP=09_ref04_static   step "$PY" -I "$HERE/review_ref04.py"
STEP=10_ref04_anim     step "$PY" -I "$HERE/anim_ref04.py"
STEP=11_anim_renders   step "$PY" -I "$HERE/anim_render.py"
# optional before/after column: FH54_PREFIX_BUILD=<build folder made before the H2/H3 behind-ear hairline change>
STEP=11b_behind_ear    step "$PY" -I "$HERE/behind_ear54.py"
STEP=12_sheets         step "$PY" -I "$HERE/compose54.py"
STEP=13_tables         step "$PY" -I "$HERE/summarize54.py"
echo "== done: $FH53_BUILD"
