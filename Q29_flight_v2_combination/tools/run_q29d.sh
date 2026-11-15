#!/bin/sh
# Q29D recordings: O2 extended + 5 pre-registered other-seed states, arms base/v2/v2x. Args: <setDir> <suiteInputsDir> <recDir> <logDir>
set -u
SET=$1; IN=$2; REC=$3; LOG=$4; T=$(cd "$(dirname "$0")" && pwd); mkdir -p "$REC" "$LOG"
run(){ id=$1; inp=$2; st=$3; en=$4
 for arm in base v2 v2x; do node "$T/record4.mjs" "$SET" "$inp" base "$st" "$en" "$arm" "$REC/${id}_$arm.json.gz" > "$LOG/record_${id}_$arm.log" 2>&1 & done; wait; }
run O2L "$SET/inputs/42130.json" 42187 42700
run N1 "$IN/otherseed_state_87312948_6122.json" 6122 6300
run N2 "$IN/outlet_to_shot.json" 78290 78515
run N3 "$IN/control_state_24263.json" 24263 24480
run N4 "$IN/otherseed_state_87312949_6039.json" 6039 6300
run N5 "$IN/postpass_state_12164.json" 12164 12300
echo q29d done
