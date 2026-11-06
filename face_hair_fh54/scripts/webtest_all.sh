#!/usr/bin/env bash
# FH54 browser test: three.js 0.186.1 in headless Chromium (Playwright) with SwiftShader. Local only, nothing published.
# Usage: FH53_BUILD=<build> FH53_REFERENCE=<FH53 extracted> FH53_INPUTS=<restored_inputs> FH53_REF04=<ref04 dir>
#        THREE_DIR=<node_modules/three> PW_NODE_MODULES=<dir containing playwright> PY=<python> bash webtest_all.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; W="$FH53_BUILD/webtest"; PORT=${PORT:-8765}
mkdir -p "$W/lib/three/build" "$W/lib/three/jsm/loaders" "$W/lib/three/jsm/utils" "$W/glb"
cp "$THREE_DIR/build/three.module.js" "$THREE_DIR/build/three.core.js" "$W/lib/three/build/"
cp "$THREE_DIR/examples/jsm/loaders/GLTFLoader.js" "$W/lib/three/jsm/loaders/"
cp "$THREE_DIR/examples/jsm/utils/BufferGeometryUtils.js" "$THREE_DIR/examples/jsm/utils/SkeletonUtils.js" "$W/lib/three/jsm/utils/"
cp "$HERE/webtest_page.html" "$W/index.html"; cp "$HERE"/webtest_run.mjs "$HERE"/webtest_sweep.mjs "$HERE"/force_order.mjs "$W/"
cp "$FH53_INPUTS/CODEX/face52_work/models/TM_FACE52_F0_H0.glb" "$W/glb/FACE52.glb"
cp "$FH53_REF04/Sakatsuku2002_reference04_APPEARANCE_STUDY.glb" "$W/glb/REF04_body.glb"
for h in H1 H2 H3 H4; do
  cp "$FH53_REFERENCE/models/combos/TM_FH53_F0_$h.glb" "$W/glb/FH53_$h.glb"
  cp "$FH53_BUILD/models/combos/TM_FH54_F0_$h.glb" "$W/glb/FH54_$h.glb"
  cp "$FH53_BUILD/models/combos/TM_FH54_F1_$h.glb" "$W/glb/FH54_F1_$h.glb"
done
ln -sfn "$PW_NODE_MODULES" "$W/node_modules"
( cd "$W" && python3 -m http.server "$PORT" --bind 127.0.0.1 > /dev/null 2>&1 & echo $! > "$W/.server.pid" ); sleep 1
trap 'kill $(cat "$W/.server.pid") 2>/dev/null || true' EXIT
( cd "$W" && node webtest_run.mjs "$W" "$PORT" && node webtest_sweep.mjs "$W" "$PORT" && node force_order.mjs "$W/force" )
"$PY" -I "$HERE/webtest_analyze.py" "$W/out" > /dev/null
"$PY" -I "$HERE/webtest_flip.py" "$W/sweep" > /dev/null
"$PY" -I - "$W" <<'PYEOF'
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
W = Path(sys.argv[1]); bg = np.array([0x3a, 0x41, 0x50], float); res = {}
for m in ['FACE52', 'FH53_H1', 'FH54_H1', 'FH53_H2', 'FH54_H2', 'FH53_H3', 'FH54_H3', 'FH53_H4', 'FH54_H4']:
    r = []
    for lab in ('q', 'top', 'back'):
        a = np.asarray(Image.open(W/f'force/{m}_{lab}_cardsLast.png').convert('RGB')).astype(float); b = np.asarray(Image.open(W/f'force/{m}_{lab}_cardsFirst.png').convert('RGB')).astype(float)
        head = (np.abs(a - bg).sum(2) > 12) | (np.abs(b - bg).sum(2) > 12); dd = np.abs(a - b).sum(2)/3
        r.append(round(100*float(((dd > 8) & head).sum()/head.sum()), 2))
    res[m] = r
(W/'force/force_order_result.json').write_text(json.dumps(res, indent=1)); print('force-order', res)
PYEOF
echo "webtest done"
