const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
    const htmlDir = path.join(__dirname, '_html');
    const outDir = __dirname;

    const htmlFiles = fs.readdirSync(htmlDir)
        .filter(f => f.endsWith('.html'))
        .sort();

    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: 1080, height: 1080 },
        deviceScaleFactor: 1,
    });

    for (let i = 0; i < htmlFiles.length; i++) {
        const htmlPath = path.join(htmlDir, htmlFiles[i]);
        const pngName = htmlFiles[i].replace('.html', '.png');
        const pngPath = path.join(outDir, pngName);

        const page = await context.newPage();
        await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle' });
        // clip to exactly 1080x1080 to prevent scrollbar/border clipping
        await page.screenshot({
            path: pngPath,
            type: 'png',
            clip: { x: 0, y: 0, width: 1080, height: 1080 }
        });
        await page.close();
        console.log(`  [${i+1}/${htmlFiles.length}] ${pngName}`);
    }

    await browser.close();
    console.log(`\nDone! ${htmlFiles.length} PNG files created`);
})();
