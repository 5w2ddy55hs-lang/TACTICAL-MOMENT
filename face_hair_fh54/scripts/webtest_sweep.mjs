// Elevation sweep (-20..85 deg, 1.5 deg steps, az 30) in authored / bounds / reference modes; records transparent draw order.
import { chromium } from 'playwright'; import fs from 'fs'; import path from 'path';
const [dir, port] = [process.argv[2], process.argv[3] || '8765']; const out = path.join(dir, 'sweep'); fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage(); await page.goto(`http://127.0.0.1:${port}/index.html`); await page.waitForFunction(() => window.READY === true);
const info = await page.evaluate(() => { const c = document.createElement('canvas').getContext('webgl'); const e = c.getExtension('WEBGL_debug_renderer_info'); return e ? c.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'n/a'; });
const res = { unmasked_renderer: info, models: {} };
const save = (name, url) => fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
for (const m of ['FACE52', 'FH53_H1', 'FH54_H1', 'FH53_H2', 'FH54_H2', 'FH53_H3', 'FH54_H3', 'FH53_H4', 'FH54_H4']) {
  res.models[m] = {};
  for (const mode of ['authored', 'bounds', 'reference']) {
    await page.evaluate(([u, md]) => window.T.load(u, md), [`glb/${m}.glb`, mode]); const orders = [];
    for (let i = 0; i < 71; i++) { const el = -20 + i*1.5; orders.push(await page.evaluate(([a, e]) => window.T.order(a, e), [30, el]));
      save(`${m}_${mode}_${String(i).padStart(3, '0')}.png`, await page.evaluate(([a, e]) => window.T.shot(a, e), [30, el])); }
    res.models[m][mode] = orders;
  }
  console.log('sweep', m);
}
fs.writeFileSync(path.join(out, 'sweep_orders.json'), JSON.stringify(res, null, 1)); await browser.close();
