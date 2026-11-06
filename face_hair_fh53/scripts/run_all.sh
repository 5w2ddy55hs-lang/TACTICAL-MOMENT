#!/usr/bin/env bash
# FH53 full pipeline. Requires: Python 3.11 with bpy==4.2.23 (PyPI wheel), numpy, scipy, Pillow.
# Usage: FH53_INPUTS=<restored_inputs> FH53_REF04=<Reference04 dir> FH53_BUILD=<new output dir> PY=<python> bash run_all.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${FH53_INPUTS:?}" "${FH53_REF04:?}" "${FH53_BUILD:?}"; PY="${PY:-python3}"
export FH53_INPUTS FH53_REF04 FH53_BUILD
mkdir -p "$FH53_BUILD/logs"
step() { echo "== $1"; shift; "$@" > "$FH53_BUILD/logs/$STEP.log" 2>&1 || { echo "FAILED: $STEP (see logs/$STEP.log)"; exit 1; }; }
STEP=00_textures   step "procedural hair textures" "$PY" -I "$HERE/make_hair_textures.py" "$FH53_BUILD/textures"
STEP=01_faces      step "face candidates F1-F3"    "$PY" -I "$HERE/build_faces.py"
STEP=02_hairs      step "hair candidates H1-H4"    "$PY" -I "$HERE/build_hairs.py"
STEP=03_combos     step "20 combos + library"      "$PY" -I "$HERE/export_combos.py"
STEP=04_verify     step "verification"             "$PY" -I "$HERE/verify_all.py"
STEP=05_skin_disp  step "face skin displacement"   "$PY" -I "$HERE/face_skin_displacement.py"
STEP=06_renders    step "renders from GLBs"        "$PY" -I "$HERE/render_all.py"
STEP=07_ref04      step "Reference04 review"       "$PY" -I "$HERE/review_ref04.py"
STEP=08_ref04sheet step "Reference04 sheet"        "$PY" -I "$HERE/compose_ref04.py"
STEP=09_tables     step "QA tables"                "$PY" -I "$HERE/summarize_qa.py"
echo "== done: $FH53_BUILD"
