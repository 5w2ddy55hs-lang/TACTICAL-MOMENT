#!/bin/sh
# Q29C candidate v2x: receive V2 (base_on) with ONE added line in reception.mjs — when the closest approach has already
# passed (tClosest<=0) AND the player's own latest WITNESSED touch was by itself, return null (= I17 behaviour).
# Everything else is V2. Own identity. usage: sh build_v2x.sh <setCopyDir>
set -eu
SET=$1; SRC=$SET/research/l21_natural/recovered/l21_receive_compare/branches/base_on; DST=$SET/research/l21_natural/recovered/l21_receive_compare/branches/q29c_v2x
[ -e "$DST" ] && { echo "exists: $DST"; exit 1; }
cp -r "$SRC" "$DST"
python3 -I - "$DST/reception.mjs" <<'PY'
import sys;p=sys.argv[1];s=open(p).read()
old=" if(tClosest>1.5)return null;\n"
new=" if(tClosest>1.5)return null;\n // Q29C RESEARCH ONLY: own pushed ball (latest witnessed touch is self) keeps the I17 generic pursuit; no V2 extension.\n if(tClosest<=0&&p.observedTouch&&p.observedTouch.players.length>0&&p.observedTouch.players.every(q=>q.id===p.id))return null;\n"
assert s.count(old)==1;open(p,'w').write(s.replace(old,new))
PY
H=$(sha256sum "$DST/reception.mjs" | cut -c1-64)
B=$(printf '%s' "Q29C_RESEARCH_V2X|v2:7328899491c397bf68d86e70e7628ca207b58e4a2a94bb23e547e06cd52cfeec|reception:$H" | sha256sum | cut -c1-64)
cat > "$DST/pass_build_identity.mjs" <<EOT
// Q29C RESEARCH ONLY (not adopted): receive V2 without the extension for the player's own pushed ball. Own identity.
export const PASS_BUILD_SHA256='$B';
export const PASS_SAVE_SCHEMA='TM_RESEARCH_Q29C_V2X_SAVE/1';
export const PASS_ENGINE='TM_RESEARCH_Q29C_V2X_PASS_R1';
export const PASS_RESULT_SCHEMA='TM_RESEARCH_Q29C_V2X_RESULT/1';
EOT
python3 -I -c "import json,sys;p=sys.argv[1];e=json.load(open(p));e['v2x']='l21_natural/recovered/l21_receive_compare/branches/q29c_v2x/engine.mjs';json.dump(e,open(p,'w'),indent=1)" "$SET/engines.json"
echo built "$DST"
