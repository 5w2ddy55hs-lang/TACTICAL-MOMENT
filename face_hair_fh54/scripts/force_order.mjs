// Worst-case transparent order test: hair cards drawn first vs last (renderOrder), same camera.
import { chromium } from 'playwright'; import fs from 'fs';
const out = process.argv[2]; const port = process.argv[3] || '8765'; fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage(); await page.goto(`http://127.0.0.1:${port}/index.html`); await page.waitForFunction(() => window.READY === true);
for (const m of ['FACE52', 'FH53_H1', 'FH54_H1', 'FH53_H2', 'FH54_H2', 'FH53_H3', 'FH54_H3', 'FH53_H4', 'FH54_H4']) {
  await page.evaluate(u => window.T.load(u, 'authored'), `glb/${m}.glb`);
  for (const [lab, az, el] of [['q', 30, 25], ['top', 0, 70], ['back', 180, 20]]) {
    for (const cf of [false, true]) {
      await page.evaluate(c => window.T.setOrder(c), cf);
      const url = await page.evaluate(([a, e]) => window.T.shot(a, e), [az, el]);
      fs.writeFileSync(`${out}/${m}_${lab}_${cf ? 'cardsFirst' : 'cardsLast'}.png`, Buffer.from(url.split(',')[1], 'base64'));
    }
  }
}
await browser.close();
