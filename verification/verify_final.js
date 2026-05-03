const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
  // Bypass intro
  await page.addInitScript(() => {
    localStorage.setItem('syndicate_live', 'true');
  });

  // Start server
  const { spawn } = require('child_process');
  const server = spawn('python3', ['-m', 'http.server', '8081']);
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
  await new Promise(resolve => setTimeout(resolve, 2000));

  try {
    console.log("Navigating to optimization page...");
    await page.goto('http://localhost:8081/optimization.html');
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
    // Check Sticky
    const widget = await page.locator('#readiness-command');
    const initialBox = await widget.boundingBox();
    console.log(`Initial Widget Y: ${initialBox.y}`);
<<<<<<< Updated upstream

    await page.evaluate(() => window.scrollTo(0, 1000));
    await page.waitForTimeout(500);

    const isCompact = await widget.evaluate(el => el.classList.contains('compact'));
    const position = await widget.evaluate(el => getComputedStyle(el).position);
    console.log(`Scrolled: isCompact=${isCompact}, position=${position}`);

    // Check Matrix Background Sync
    await page.goto('http://localhost:8081/index.html');
    const matrixBg = await page.evaluate(() => {
        // We can't easily check canvas state, but we can check the matrixBgColor variable if exposed,
=======

    await page.evaluate(() => window.scrollTo(0, 1000));
    await page.waitForTimeout(500);

    const isCompact = await widget.evaluate(el => el.classList.contains('compact'));
    const position = await widget.evaluate(el => getComputedStyle(el).position);
    console.log(`Scrolled: isCompact=${isCompact}, position=${position}`);

    // Check Matrix Background Sync
    await page.goto('http://localhost:8081/index.html');
    const matrixBg = await page.evaluate(() => {
        // We can't easily check canvas state, but we can check the matrixBgColor variable if exposed,
>>>>>>> Stashed changes
        // or just ensure no errors and the canvas exists.
        return typeof matrixBgColor !== 'undefined' ? matrixBgColor : 'not_exposed';
    });
    console.log(`Matrix Background Variable: ${matrixBg}`);
<<<<<<< Updated upstream

    await page.screenshot({ path: 'verification/final_dark.png' });

    await page.click('#theme-toggle');
    await page.waitForTimeout(200);
    await page.screenshot({ path: 'verification/final_light.png' });

=======

    await page.screenshot({ path: 'verification/final_dark.png' });

    await page.click('#theme-toggle');
    await page.waitForTimeout(200);
    await page.screenshot({ path: 'verification/final_light.png' });

>>>>>>> Stashed changes
  } catch (e) {
    console.error(e);
  } finally {
    server.kill();
    await browser.close();
  }
})();
