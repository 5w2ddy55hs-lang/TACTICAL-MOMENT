#!/usr/bin/env bash
# HM56 browser test (representative player, continuous clip playback) (three.js, headless Chromium + SwiftShader) and Khronos glTF Validator. Local only, nothing published.
# Usage: HM_BUILD=<build> THREE_DIR=<node_modules/three> PW_NODE_MODULES=<dir containing playwright> PY=<python>
#        [VALIDATOR_NODE_MODULES=<dir containing gltf-validator>] bash webtest56.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; W="$HM_BUILD/webtest"; PORT=${PORT:-8766}; mkdir -p "$HM_BUILD/qa" "$HM_BUILD/logs"
if [ -n "${VALIDATOR_NODE_MODULES:-}" ]; then
  V="$HM_BUILD/validator"; mkdir -p "$V"; cp "$HERE/gltf_validate.mjs" "$V/"; ln -sfn "$VALIDATOR_NODE_MODULES" "$V/node_modules"
  node "$V/gltf_validate.mjs" "$HM_BUILD"/models/players/*.glb "$HM_BUILD"/models/modules/*.glb > "$HM_BUILD/qa/gltf_validator.json"
  echo "validator: $(grep -c '"errors"' "$HM_BUILD/qa/gltf_validator.json") files"
fi
rm -rf "$W/out" "$W/glb"; mkdir -p "$W/lib/three/build" "$W/lib/three/jsm/loaders" "$W/lib/three/jsm/utils" "$W/glb"
cp "$THREE_DIR/build/three.module.js" "$THREE_DIR/build/three.core.js" "$W/lib/three/build/"
cp "$THREE_DIR/examples/jsm/loaders/GLTFLoader.js" "$W/lib/three/jsm/loaders/"
cp "$THREE_DIR/examples/jsm/utils/BufferGeometryUtils.js" "$THREE_DIR/examples/jsm/utils/SkeletonUtils.js" "$W/lib/three/jsm/utils/"
node -e "console.log(JSON.stringify({version: require('$THREE_DIR/package.json').version}))" > "$W/three_version.json"
cp "$HERE/webtest55_page.html" "$W/index.html"; cp "$HERE/webtest56_run.mjs" "$W/"
cp "$HM_BUILD/models/players/TM_HM56_PLAYER_P0_H2_KITA.glb" "$W/glb/"
ln -sfn "$PW_NODE_MODULES" "$W/node_modules"
( cd "$W" && python3 -m http.server "$PORT" --bind 127.0.0.1 > /dev/null 2>&1 & echo $! > "$W/.server.pid" ); sleep 1
trap 'kill $(cat "$W/.server.pid") 2>/dev/null || true' EXIT
( cd "$W" && node webtest56_run.mjs "$W" "$PORT" )
for c in "$W"/out/play/*/*/; do c="${c%/}"; ffmpeg -y -loglevel error -framerate 30 -i "$c/%04d.png" -c:v libx264 -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" "$c.mp4"; done
mkdir -p "$HM_BUILD/video"; ( cd "$W/out/play" && for f in */*.mp4; do echo "file '$PWD/$f'"; done ) > "$W/out/play/list.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$W/out/play/list.txt" -c copy -movflags +faststart "$HM_BUILD/video/HM56_browser_threejs_playback.mp4"
cp "$W/out/webtest55_result.json" "$HM_BUILD/qa/webtest55_result.json"
"$PY" -I "$HERE/webtest55_analyze.py"
echo "webtest done"
