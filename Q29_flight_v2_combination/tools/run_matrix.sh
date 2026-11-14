#!/bin/sh
# Q29: 5 opportunities x 4 arms from a common start (record4.mjs). Args: <setDir> <recDir> <logDir>
set -u
SET=$1; REC=$2; LOG=$3; T=$(cd "$(dirname "$0")" && pwd); mkdir -p "$REC" "$LOG"
run(){ id=$1; inp=$2; src=$3; st=$4; en=$5
 for arm in base flight v2 combo; do node "$T/record4.mjs" "$SET" "$SET/inputs/$inp.json" "$src" "$st" "$en" "$arm" "$REC/${id}_$arm.json.gz" > "$LOG/record_${id}_$arm.log" 2>&1 & done; wait; }
run O1 42130 base 42130 42400
run O2 42130 base 42187 42400
run O3 12235 base 12340 12500
run O4 60000 base 60000 60400
run O5 60000 flight 60269 60400
echo matrix done
