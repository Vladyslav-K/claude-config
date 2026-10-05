// Prints <html-dir>/<name>.html to <out-dir>/<name>.pdf for every name, in its own headless Chromium.
// Usage: node print.js <html-dir> <out-dir> <name>...
const path = require('path');

const PLAYWRIGHT_CORE = '/usr/local/lib/node_modules/@playwright/mcp/node_modules/playwright-core';
const { chromium } = require(PLAYWRIGHT_CORE);

const [htmlDir, outDir, ...names] = process.argv.slice(2);
if (!htmlDir || !outDir || names.length === 0) {
  console.error('usage: node print.js <html-dir> <out-dir> <name>...');
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    for (const name of names) {
      await page.goto(`file://${path.resolve(htmlDir, `${name}.html`)}`, { waitUntil: 'load' });
      await page.pdf({
        path: path.resolve(outDir, `${name}.pdf`),
        format: 'A4',
        printBackground: true,
        margin: { top: '14mm', bottom: '14mm', left: '12mm', right: '12mm' },
        displayHeaderFooter: true,
        headerTemplate: '<span></span>',
        footerTemplate:
          '<div style="font-size:8px;width:100%;text-align:center;color:#64748b"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
      });
      console.log('ok', name);
    }
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
