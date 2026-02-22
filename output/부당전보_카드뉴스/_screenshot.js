const { chromium } = require('playwright');
(async () => {
    const pairs = [{"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_01_cover.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_01_cover.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_02_problem.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_02_problem.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_03_point.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_03_point.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_04_point.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_04_point.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_05_comparison.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_05_comparison.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_06_point.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_06_point.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_07_summary.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_07_summary.png"}, {"html": "C:/workspace/blog-post/output/부당전보_카드뉴스/_html/부당전보대응_08_cta.html", "png": "C:/workspace/blog-post/output/부당전보_카드뉴스/부당전보대응_08_cta.png"}];
    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: 1080, height: 1080 },
        deviceScaleFactor: 1,
    });
    for (let i = 0; i < pairs.length; i++) {
        const page = await context.newPage();
        await page.goto('file:///' + pairs[i].html, { waitUntil: 'networkidle' });
        await page.screenshot({ path: pairs[i].png, type: 'png' });
        await page.close();
        console.log('  ✅ [' + (i+1) + '/' + pairs.length + '] ' + pairs[i].png.split('/').pop());
    }
    await browser.close();
    console.log('\n🎉 카드뉴스 ' + pairs.length + '장 PNG 생성 완료!');
})();
