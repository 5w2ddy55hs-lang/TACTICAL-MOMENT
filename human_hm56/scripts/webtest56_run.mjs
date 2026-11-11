// HM55 browser test driver (three.js in headless Chromium via Playwright, SwiftShader software rendering). Local only.
// Usage: node webtest56_run.mjs WEBTEST_DIR PORT
import { chromium } from 'playwright';
import fs from 'fs'; import path from 'path';
const [dir, port] = [process.argv[2], process.argv[3] || '8766'];
const out = path.join(dir, 'out'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } }); const errors = [];
page.on('console', m => { if (m.type() === 'error') { errors.push(m.text()); console.log('PAGE ERR', m.text()); } });
await page.goto(`http://127.0.0.1:${port}/index.html`); await page.waitForFunction(() => window.READY === true);
const save = (name, url) => fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
const models = fs.readdirSync(path.join(dir, 'glb')).filter(f => f.endsWith('.glb')).map(f => f.replace('.glb', '')).sort();
const result = { three: JSON.parse(fs.readFileSync(path.join(dir, 'three_version.json'))).version, models: {}, perf: {}, page_errors: errors };
const SHOTS = [['TM_HM55_Run', [0.0, 0.167, 0.333, 0.5]], ['TM_HM55_Kick', [0.267, 0.467, 0.633, 0.833]], ['TM_HM55_LookAround', [0.5, 1.5, 2.333, 2.667]], ['TM_HM55_ThrowIn', [0.433, 0.667]], ['TM_HM55_Header', [0.567, 0.7]]];
for (const m of models) {
  const info = await page.evaluate(u => window.T.load(u), `glb/${m}.glb`); result.models[m] = info;
  await page.evaluate(() => window.T.pose(null, 0));
  for (const [lab, az] of [['front', 0], ['side', 90], ['back', 180]]) save(`${m}_rest_${lab}.png`, await page.evaluate(([a]) => window.T.shot(a, 5, 6.2, 0.92), [az]));
  for (const [clip, times] of SHOTS) for (const t of times) {
    await page.evaluate(([c, tt]) => window.T.pose(c, tt), [clip, t]); const h = await page.evaluate(() => window.T.hips());
    for (const [lab, az] of [['q', 35], ['side', 90]]) save(`${m}_${clip.replace('TM_HM55_', '')}_${String(Math.round(t*1000)).padStart(4, '0')}_${lab}.png`, await page.evaluate(([a, y]) => window.T.shot(a, 8, 6.6, y), [az, 0.95]));
  }
  // continuous playback in the browser: every frame (1/30 s) of four clips through three.js AnimationMixer
  for (const clip of ['TM_HM55_Run', 'TM_HM55_Kick', 'TM_HM55_Header', 'TM_HM55_LookAround']) {
    const dur = info.clips.find(c => c.name === clip).duration; const n = Math.round(dur*30) + 1; fs.mkdirSync(path.join(out, 'play', m, clip), { recursive: true });
    for (let k = 0; k < n; k++) { await page.evaluate(([c, tt]) => window.T.pose(c, tt), [clip, k/30]);
      fs.writeFileSync(path.join(out, 'play', m, clip, String(k).padStart(4, '0') + '.png'), Buffer.from((await page.evaluate(() => window.T.shot(35, 8, 6.6, 0.95))).split(',')[1], 'base64')); }
    result.models[m].playback = (result.models[m].playback || {}); result.models[m].playback[clip] = n;
  }
  // orbit around the head (hair transparency), default order vs cards drawn first (worst case), and back-face culling on the body
  await page.evaluate(() => window.T.pose(null, 0));
  for (const cf of [false, true]) { await page.evaluate(c => window.T.setOrder(c), cf);
    for (const [lab, az, el] of [['q', 30, 25], ['top', 0, 70], ['back', 180, 20], ['side', 90, 5]]) save(`${m}_order_${lab}_${cf ? 'cardsFirst' : 'cardsLast'}.png`, await page.evaluate(([a, e]) => window.T.shot(a, e, 1.25, 1.68), [az, el])); }
  await page.evaluate(c => window.T.setOrder(c), false);
  for (const fs_ of [true, false]) { await page.evaluate(f => window.T.setSide(f), fs_); await page.evaluate(([c, tt]) => window.T.pose(c, tt), ['TM_HM55_Kick', 0.833]);
    save(`${m}_side_${fs_ ? 'frontOnly' : 'double'}.png`, await page.evaluate(() => window.T.shot(35, 8, 6.6, 0.95))); }
  console.log('done', m);
}
for (const [lab, clip] of [['x22_idle', 'TM_HM55_Idle'], ['x22_run', 'TM_HM55_Run']]) {
  const r = await page.evaluate(([u, c]) => window.T.perf(u, 22, 120, c), [`glb/${models[0]}.glb`, clip]); save(`perf_${lab}.png`, r.image); delete r.image; result.perf[models[0] + '_' + lab] = r; console.log('perf', lab, JSON.stringify(r));
}
fs.writeFileSync(path.join(out, 'webtest55_result.json'), JSON.stringify(result, null, 1)); await browser.close();
