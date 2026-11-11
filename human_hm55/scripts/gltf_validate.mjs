// Khronos glTF Validator over the given GLB files; prints one JSON object (errors/warnings/infos/hints + first 30 E/W messages).
// Usage: node gltf_validate.mjs <glb>... (needs the npm package gltf-validator next to this file, e.g. via a node_modules link)
import fs from 'fs'; import path from 'path'; import validator from 'gltf-validator';
const files = process.argv.slice(2); const out = {};
for (const f of files) {
  const data = new Uint8Array(fs.readFileSync(f));
  const r = await validator.validateBytes(data, { uri: path.basename(f), maxIssues: 200 });
  out[path.basename(f)] = { errors: r.issues.numErrors, warnings: r.issues.numWarnings, infos: r.issues.numInfos, hints: r.issues.numHints,
    messages: r.issues.messages.filter(m => m.severity <= 1).map(m => `${m.severity === 0 ? 'E' : 'W'} ${m.code} ${m.pointer || ''} ${m.message}`).slice(0, 30),
    validatorVersion: r.validatorVersion };
}
console.log(JSON.stringify(out, null, 1));
