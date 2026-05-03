const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Bypass intro
  await page.addInitScript(() => {
    localStorage.setItem('syndicate_live', 'true');
  });

  // Start server
  const { spawn } = require('child_process');
  const server = spawn('python3', ['-m', 'http.server', '8081']);

  await new Promise(resolve => setTimeout(resolve, 2000));

  try {
    console.log("Navigating to optimization page...");
    await page.goto('http://localhost:8081/optimization.html');

    // Check Sticky
    const widget = await page.locator('#readiness-command');
    const initialBox = await widget.boundingBox();
    console.log(`Initial Widget Y: ${initialBox.y}`);

    await page.evaluate(() => window.scrollTo(0, 1000));
    await page.waitForTimeout(500);

    const isCompact = await widget.evaluate(el => el.classList.contains('compact'));
    const position = await widget.evaluate(el => getComputedStyle(el).position);
    console.log(`Scrolled: isCompact=${isCompact}, position=${position}`);

    // Check Matrix Background Sync
    await page.goto('http://localhost:8081/index.html');
    const matrixBg = await page.evaluate(() => {
        // We can't easily check canvas state, but we can check the matrixBgColor variable if exposed,
        // or just ensure no errors and the canvas exists.
        return typeof matrixBgColor !== 'undefined' ? matrixBgColor : 'not_exposed';
    });
    console.log(`Matrix Background Variable: ${matrixBg}`);

    await page.screenshot({ path: 'verification/final_dark.png' });

    await page.click('#theme-toggle');
    await page.waitForTimeout(200);
    await page.screenshot({ path: 'verification/final_light.png' });

  } catch (e) {
    console.error(e);
  } finally {
    server.kill();
    await browser.close();
  }
})();
