import time
import subprocess
import re
from playwright.sync_api import sync_playwright, expect

def verify():
    # Start server
    server = subprocess.Popen(['python3', '-m', 'http.server', '8082'])
    time.sleep(2)
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
<<<<<<< Updated upstream

            # Bypass intro
            page.add_init_script("localStorage.setItem('syndicate_live', 'true')")

            # 1. Verify Sticky Widget on Optimization page
            print("Navigating to optimization page...")
            page.goto('http://localhost:8082/optimization.html')

            widget = page.locator('#readiness-command')

            # Scroll down
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(0.5)

            # Check compact state (regex)
            expect(widget).to_have_class(re.compile(r"compact"))
            print("Sticky widget verified.")

            # 2. Verify Matrix Gutter Sync on Index page
            print("Navigating to index page...")
            page.goto('http://localhost:8082/index.html')

            # Take screenshots in both modes
            page.screenshot(path='verification/final_dark_gutters.png')
            print("Dark mode screenshot captured.")

=======

            # Bypass intro
            page.add_init_script("localStorage.setItem('syndicate_live', 'true')")

            # 1. Verify Sticky Widget on Optimization page
            print("Navigating to optimization page...")
            page.goto('http://localhost:8082/optimization.html')

            widget = page.locator('#readiness-command')

            # Scroll down
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(0.5)

            # Check compact state (regex)
            expect(widget).to_have_class(re.compile(r"compact"))
            print("Sticky widget verified.")

            # 2. Verify Matrix Gutter Sync on Index page
            print("Navigating to index page...")
            page.goto('http://localhost:8082/index.html')

            # Take screenshots in both modes
            page.screenshot(path='verification/final_dark_gutters.png')
            print("Dark mode screenshot captured.")

>>>>>>> Stashed changes
            # Toggle light mode
            page.click('#theme-toggle')
            time.sleep(0.5)
            page.screenshot(path='verification/final_light_gutters.png')
            print("Light mode screenshot captured.")
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
            print("Verification successful.")
            browser.close()
    finally:
        server.kill()

if __name__ == "__main__":
    verify()
