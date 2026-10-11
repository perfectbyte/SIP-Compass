// Runs the app's built-in self-test in a headless browser. No network: fund data and fonts are stubbed.
// Usage: npm i -D playwright && npx playwright install chromium && node scripts/run-selftest.mjs
import { chromium } from 'playwright';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const app = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'SIP-Compass.html');
const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const page = await browser.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.route(/mfapi\.in|fonts\.(googleapis|gstatic)\.com|amfiindia\.com/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
await page.goto(pathToFileURL(app).href);
await page.waitForTimeout(1500);
const report = await page.evaluate(async () => String(await runSelfTest()));
await browser.close();
const fails = report.split('\n').filter(l => l.startsWith('FAIL'));
console.log(fails.join('\n'));
console.log(report.trim().split('\n').pop());
if (errors.length) console.log('Page errors:\n' + errors.join('\n'));
process.exit(fails.length || errors.length || !/(^|\n)0 failed,/.test(report) ? 1 : 0);
