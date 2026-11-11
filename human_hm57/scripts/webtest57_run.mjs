// HM57 browser test driver (three.js in headless Chromium via Playwright, SwiftShader software rendering - no GPU). Local only.
// 1. full and LITE player GLBs: structure, continuous frame-by-frame playback of Run / Kick / Header / ThrowIn / LookAround
// 2. parts swap: body + head + hair MODULE GLBs bound to one skeleton by bone name, compared pixel by pixel with the
//    assembled player at the same poses; then the kit material is swapped to kit B
// 3. 22 players at once (full vs LITE), draw calls / triangles / ms per frame (software rendering: relative numbers only)
// Usage: node webtest57_run.mjs WEBTEST_DIR PORT
import { chromium } from 'playwright';
import fs from 'fs'; import path from 'path';
const [dir, port] = [process.argv[2], process.argv[3] || '8767'];
const out = path.join(dir, 'out'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } }); const errors = [];
page.on('console', m => { if (m.type() === 'error') { errors.push(m.text()); console.log('PAGE ERR', m.text()); } });
await page.goto(`http://127.0.0.1:${port}/index.html`); await page.waitForFunction(() => window.READY === true);
const save = (name, url) => { const p = path.join(out, name); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, Buffer.from(url.split(',')[1], 'base64')); };
const players = fs.readdirSync(path.join(dir, 'glb')).filter(f => f.endsWith('.glb')).map(f => f.replace('.glb', '')).sort();
const mods = fs.readdirSync(path.join(dir, 'glb', 'modules')).filter(f => f.endsWith('.glb')).sort();
const result = { three: JSON.parse(fs.readFileSync(path.join(dir, 'three_version.json'))).version, models: {}, swap: {}, perf: {}, page_errors: errors };
const CLIPS = ['TM_HM55_Run', 'TM_HM55_Kick', 'TM_HM55_Header', 'TM_HM55_ThrowIn', 'TM_HM55_LookAround'];
for (const m of players) {
  const info = await page.evaluate(u => window.T.load(u), `glb/${m}.glb`); result.models[m] = info;
  for (const clip of CLIPS) {
    const dur = info.clips.find(c => c.name === clip).duration; const n = Math.round(dur*30) + 1;
    for (let k = 0; k < n; k++) { await page.evaluate(([c, tt]) => window.T.pose(c, tt), [clip, k/30]);
      save(`play/${m}/${clip}/${String(k).padStart(4, '0')}.png`, await page.evaluate(() => window.T.shot(35, 8, 6.6, 0.95))); }
    result.models[m].playback = (result.models[m].playback || {}); result.models[m].playback[clip] = n;
  }
  console.log('done', m);
}
// ---- parts swap
const full = players.find(p => !p.endsWith('_LITE')); const body = mods.find(f => /BODY_KITA/.test(f)), bodyB = mods.find(f => /BODY_KITB/.test(f));
const head = mods.find(f => /HEAD_/.test(f)), hair = mods.find(f => /HAIR_/.test(f));
const POSES = [['TM_HM55_Run', 0.167], ['TM_HM55_Kick', 0.633], ['TM_HM55_Header', 0.7], ['TM_HM55_LookAround', 0.5]];
const shots = {};
await page.evaluate(u => window.T.load(u), `glb/${full}.glb`);
for (const [c, t] of POSES) { await page.evaluate(([c, t]) => window.T.pose(c, t), [c, t]); shots[`player_${c}_${t}`] = await page.evaluate(() => window.T.shot(35, 8, 6.6, 0.95)); save(`swap/player_${c.replace('TM_HM55_', '')}.png`, shots[`player_${c}_${t}`]); }
result.swap.assemble = await page.evaluate(u => window.T.assemble(u), [`glb/modules/${body}`, `glb/modules/${head}`, `glb/modules/${hair}`]);
result.swap.modules = [body, head, hair]; result.swap.diff_vs_player_pct = {};
for (const [c, t] of POSES) { await page.evaluate(([c, t]) => window.T.pose(c, t), [c, t]); const a = await page.evaluate(() => window.T.shot(35, 8, 6.6, 0.95)); save(`swap/modules_${c.replace('TM_HM55_', '')}.png`, a);
  result.swap.diff_vs_player_pct[c] = await page.evaluate(async ([u1, u2]) => {
    const load = u => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = u; }); const [A, B] = await Promise.all([load(u1), load(u2)]);
    const cv = document.createElement('canvas'); cv.width = A.width; cv.height = A.height; const x = cv.getContext('2d');
    x.drawImage(A, 0, 0); const da = x.getImageData(0, 0, A.width, A.height).data; x.drawImage(B, 0, 0); const db = x.getImageData(0, 0, A.width, A.height).data; let n = 0;
    for (let i = 0; i < da.length; i += 4) if (Math.abs(da[i] - db[i]) + Math.abs(da[i + 1] - db[i + 1]) + Math.abs(da[i + 2] - db[i + 2]) > 24) n++;
    return Math.round(10000*n/(da.length/4))/100; }, [shots[`player_${c}_${t}`], a]); }
result.swap.kit_swap = await page.evaluate(u => window.T.swapKit(u), `glb/modules/${bodyB}`);
for (const [c, t] of POSES.slice(0, 2)) { await page.evaluate(([c, t]) => window.T.pose(c, t), [c, t]); save(`swap/modules_kitB_${c.replace('TM_HM55_', '')}.png`, await page.evaluate(() => window.T.shot(35, 8, 6.6, 0.95))); }
console.log('swap', JSON.stringify(result.swap));
// ---- 22 players
for (const m of players) for (const [lab, clip] of [['x22_run', 'TM_HM55_Run']]) {
  const r = await page.evaluate(([u, c]) => window.T.perf(u, 22, 120, c), [`glb/${m}.glb`, clip]); save(`perf_${m}_${lab}.png`, r.image); delete r.image; result.perf[m + '_' + lab] = r; console.log('perf', m, lab, JSON.stringify(r));
}
fs.writeFileSync(path.join(out, 'webtest57_result.json'), JSON.stringify(result, null, 1)); await browser.close();
