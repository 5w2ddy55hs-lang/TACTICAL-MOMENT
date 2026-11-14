#!/bin/sh
# Q28 reproduction. Args: <I17 core dir> <fallback pack dir (extracted, read-only)> <addendum dir> <7-scene suite root> <V2 reception.mjs> <out dir>
# Node 22+ and Python 3. All inputs are read-only; outputs go to <out dir>.
set -eu
CORE=$1; FB=$2; ADD=$3; SUITE=$4; V2=$5; OUT=$6; T=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
# 1) attached pack's own check/verify on a copy
rm -rf "$OUT/run_fb"; cp -r "$FB" "$OUT/run_fb"; (cd "$OUT/run_fb" && node --permission --allow-fs-read="$PWD" --allow-fs-write="$PWD" check.mjs && node --permission --allow-fs-read="$PWD" --allow-fs-write="$PWD" verify.mjs) > "$OUT/pack_check_verify.log" 2>&1
# 2) addendum diagnose on a copy, compared byte-for-byte
rm -rf "$OUT/run_add"; mkdir -p "$OUT/run_add"; cp "$ADD/diagnose.mjs" "$OUT/run_add/"; (cd "$OUT/run_add" && node --permission --allow-fs-read="$PWD" --allow-fs-read="$SUITE" --allow-fs-write="$PWD" diagnose.mjs "$SUITE" > diagnose.txt)
{ sha256sum "$OUT/run_add/same_target.json" "$OUT/run_add/diagnose.txt"; cmp "$OUT/run_add/diagnose.txt" "$ADD/diagnose.txt" && echo diagnose.txt identical; cmp "$OUT/run_add/same_target.json" "$ADD/same_target.json" && echo same_target.json identical; } > "$OUT/addendum_reproduce.log"
# 3) independent audits
node "$T/audit_fb.mjs" "$CORE" "$FB/input.json.gz" "$OUT/audit_fb.json" > "$OUT/audit_fb.log"
python3 -I "$T/summarize_fb.py" "$OUT/audit_fb.json" > "$OUT/summary_fb.log"
python3 -I "$T/summarize_fb2.py" "$OUT/audit_fb.json" > "$OUT/summary_fb2.log"
python3 -I "$T/heading_spread.py" "$OUT/audit_fb.json" "$FB/input.json.gz" > "$OUT/heading_spread.log"
python3 -I "$T/misc_checks.py" "$FB/input.json.gz" "$OUT/audit_fb.json" > "$OUT/misc_checks.log"
python3 -I "$T/tclosest.py" "$FB/input.json.gz" "$OUT/audit_fb.json" > "$OUT/tclosest.log"
python3 -I "$T/intended_passes.py" "$OUT/audit_fb.json" "$FB/input.json.gz" "$OUT/intended_passes.json" > "$OUT/intended_passes.log"
python3 -I "$T/dec_keys.py" "$FB/input.json.gz" > "$OUT/decision_fields.log"
node "$T/existing_cover.mjs" "$CORE" "$V2" "$FB/input.json.gz" "$OUT/audit_fb.json" "$OUT/existing_cover.json" > "$OUT/existing_cover.log"
python3 -I "$T/zonal_scope.py" "$FB/input.json.gz" "$OUT/audit_fb.json" > "$OUT/zonal_scope.log"
python3 -I "$T/crosscheck_overlap.py" "$FB/input.json.gz" "$SUITE" > "$OUT/crosscheck_overlap.log"
node "$T/audit_suite.mjs" "$CORE" "$SUITE" "$OUT/audit_suite.json" > "$OUT/audit_suite.log"
python3 -I "$T/suite_passes.py" "$OUT/audit_suite.json" "$SUITE" "$OUT/suite_passes.json" > "$OUT/suite_passes.log"
python3 -I "$T/suite_roles.py" "$OUT/audit_suite.json" "$SUITE" > "$OUT/suite_roles.log"
node "$T/ou_timeline.mjs" "$CORE" "$SUITE" outlet_unreached A10 42186 42262 > "$OUT/timeline_outlet_unreached_A10.txt"
node "$T/gate_suite.mjs" "$CORE" "$SUITE" outlet_unreached A10 42190 42250 > "$OUT/gate_outlet_unreached_A10.txt"
rm -rf "$OUT/run_fb" "$OUT/run_add/same_target.json"
echo done
