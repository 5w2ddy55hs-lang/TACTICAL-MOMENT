#!/bin/sh
# Build the Q29 research combination (flight-time lead + receive V2) as an isolated copy inside a COPY of the 3-version set.
# Only 4 changes vs the flight tree: +core/reception_v2.mjs (V2 reception, 2 import paths localised), +core/decision_v2.mjs
# (flight decision with the reception import redirected), engine.mjs decision import (1 line), own pass_build_identity.mjs.
# usage: sh build_combo.sh <setCopyDir>   (never run on the original extraction)
set -eu
SET=$1; F=$SET/research/breakthrough_support/code/pass_prediction/source; C=$SET/research/q29_combo/source; V2=$SET/research/l21_natural/recovered/l21_receive_compare/branches/base_on
[ -e "$C" ] && { echo "exists: $C"; exit 1; }
mkdir -p "$(dirname "$C")"; cp -r "$F" "$C"; CC=$C/integration_i8_standard/core
sed -e "s#'../../../playtest_i17/source/integration_i8_standard/core/math.mjs'#'./math.mjs'#" -e "s#'../../../playtest_i17/source/integration_i8_standard/core/kinematics.mjs'#'./kinematics.mjs'#" "$V2/reception.mjs" > "$CC/reception_v2.mjs"
sed -e "s#from './reception.mjs'#from './reception_v2.mjs'#" "$CC/decision.mjs" > "$CC/decision_v2.mjs"
sed -i -e "s#import {choose} from './decision.mjs';#import {choose} from './decision_v2.mjs';#" "$CC/engine.mjs"
H=$(cat "$CC/reception_v2.mjs" "$CC/decision_v2.mjs" "$CC/engine.mjs" | sha256sum | cut -c1-64)
B=$(printf '%s' "Q29_RESEARCH_COMBO|flight:491f025ba3d76d8d2869943b0853b2757cc0da335b563c6066e071cfd8ac9c9a|v2:7328899491c397bf68d86e70e7628ca207b58e4a2a94bb23e547e06cd52cfeec|files:$H" | sha256sum | cut -c1-64)
cat > "$CC/pass_build_identity.mjs" <<EOT
// Q29 RESEARCH ONLY (not adopted, not integrated): existing flight-time lead (pass_prediction/source) + existing receive V2
// (l21 base_on reception) on the engine decision path only. Own identity so no other version's save is accepted or produced.
// PASS_BUILD_SHA256 = sha256("Q29_RESEARCH_COMBO|flight:<flight build>|v2:<v2 build>|files:<sha256(reception_v2+decision_v2+engine)>")
export const PASS_BUILD_SHA256='$B';
export const PASS_SAVE_SCHEMA='TM_RESEARCH_Q29_FLIGHT_V2_COMBO_SAVE/1';
export const PASS_ENGINE='TM_RESEARCH_Q29_FLIGHT_V2_COMBO_PASS_R1';
export const PASS_RESULT_SCHEMA='TM_RESEARCH_Q29_FLIGHT_V2_COMBO_RESULT/1';
EOT
python3 -I -c "import json,sys;p=sys.argv[1];e=json.load(open(p));e['combo']='q29_combo/source/integration_i8_standard/core/engine.mjs';json.dump(e,open(p,'w'),indent=1)" "$SET/engines.json"
echo built "$C"
