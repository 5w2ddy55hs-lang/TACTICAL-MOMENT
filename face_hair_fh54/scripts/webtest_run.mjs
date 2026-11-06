// FH54 browser test driver (three.js r186.1 in headless Chromium via Playwright). Local only.
// Usage: node webtest_run.mjs WEBTEST_DIR PORT
import { chromium } from 'playwright';
import fs from 'fs'; import path from 'path';
const [dir, port] = [process.argv[2], process.argv[3] || '8765'];
const out = path.join(dir, 'out'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
page.on('console', m => { if (m.type() === 'error') console.log('PAGE ERR', m.text()); });
await page.goto(`http://127.0.0.1:${port}/index.html`); await page.waitForFunction(() => window.READY === true);
const models = ['FACE52', 'FH53_H1', 'FH54_H1', 'FH53_H2', 'FH54_H2', 'FH53_H3', 'FH54_H3', 'FH53_H4', 'FH54_H4'];
const save = (name, url) => fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
const result = { three: '0.186.1', models: {}, perf: {} };
for (const m of models) {
  result.models[m] = {};
  for (const mode of ['authored', 'bounds', 'reference']) {
    const prims = await page.evaluate(([u, md]) => window.T.load(u, md), [`glb/${m}.glb`, mode]);
    result.models[m][mode] = prims;
    for (let i = 0; i < 120; i++) { const url = await page.evaluate(([a]) => window.T.shot(a, 10), [i*3]); save(`${m}_${mode}_${String(i).padStart(3, '0')}.png`, url); }
    for (const [lab, az, el] of [['top', 0, 70], ['back_high', 180, 35]]) { const url = await page.evaluate(([a, e]) => window.T.shot(a, e), [az, el]); save(`${m}_${mode}_${lab}.png`, url); }
  }
  console.log('done', m);
}
for (const [lab, glb, body] of [['FACE52_x22', 'FACE52', null], ['FH53_H1_x22', 'FH53_H1', null], ['FH54_H1_x22', 'FH54_H1', null], ['FH54_H4_x22', 'FH54_H4', null],
                                 ['FACE52_x22_with_body', 'FACE52', 'glb/REF04_body.glb'], ['FH54_F1_H1_x22_with_body', 'FH54_F1_H1', 'glb/REF04_body.glb']]) {
  result.perf[lab] = await page.evaluate(([u, b]) => window.T.perf(u, 22, 200, b), [`glb/${glb}.glb`, body]);
  console.log('perf', lab, JSON.stringify(result.perf[lab]));
}
fs.writeFileSync(path.join(out, 'webtest_result.json'), JSON.stringify(result, null, 1));
await browser.close();
