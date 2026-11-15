#!/bin/sh
# Q29D analysis over rec_d (read only). Args: <setDir> <recDir> <outDir>
set -u
SET=$1; REC=$2; OUT=$3; T=$(cd "$(dirname "$0")" && pwd); mkdir -p "$OUT"
python3 -I - "$OUT" <<'EOF'
import json,glob,sys,os
out=sys.argv[1]
with open(os.path.join(out,'C3_q29d_runs_summary.txt'),'w') as w:
    for f in sorted(glob.glob(os.path.join(out,'record_*.log'))):
        try:r=json.loads(open(f).read().strip().splitlines()[-1])
        except Exception as e:w.write(f"{os.path.basename(f)} UNREADABLE {e}\n");continue
        w.write(f"{os.path.basename(f)} start {r['startTick']} fixture {r['fixture']} nativeExact {r.get('nativeExact')} ownSaveRestore {r.get('ownSaveRestore')} restore20 {r.get('restore20')} startNative {r['startNativeSha256'][:12]} rows {r.get('rows')} endNative {str(r.get('endNativeSHA'))[:12]}\n")
EOF
for id in O2L N1 N2 N3 N4 N5; do
 { echo "## $id"; for pair in "v2 base" "v2x base" "v2x v2"; do set -- $pair; echo "-- $1 vs $2"; python3 -I "$T/first_divergence.py" "$REC/${id}_$1.json.gz" "$REC/${id}_$2.json.gz" | head -3; done; } > "$OUT/divergence_$id.txt" 2>&1
 node "$T/trace_arms.mjs" "$SET" "$REC" "$id" "$OUT/trace_$id.json" base,v2,v2x > "$OUT/trace_$id.txt" 2>&1
 for arm in v2 v2x; do node "$T/v2only_episodes.mjs" "$SET" "$REC/${id}_$arm.json.gz" "${id}_$arm" all "$OUT/v2only_${id}_$arm.json" > "$OUT/v2only_${id}_$arm.txt" 2>&1; done
done
echo analysis done
