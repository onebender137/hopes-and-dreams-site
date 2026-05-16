import os
import re

# Define the synchronized footer layout
NEW_FOOTER = """<footer>
    <p>&copy; 2026 Dream Syndicate Digital Assets. All Rights Reserved.</p>
    <p>
        <a href="https://www.facebook.com/profile.php?id=61581034972328" target="_blank" rel="noopener noreferrer">Connect on Facebook</a> |
        <a href="https://merch.hopes-and-dreams.ca" target="_blank" rel="noopener noreferrer">Merch</a> |
        <a href="intel.html">Intel Hub</a> |
        <a href="optimization.html">Tools</a> |
        <a href="privacy.html">Privacy Policy</a> |
        <a href="about.html">Contact Us</a>
    </p>
    <p style="font-size: 0.7rem; color: var(--text-dim); margin-top: 10px;">Location: Saint John, New Brunswick, Canada</p>
</footer>"""

def sync_clean_nav():
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    modified_count = 0
    
    # The ultimate clean, scannable horizontal line-up
    standard_nav = """<nav>
            <a href="index.html">Home</a>
            <a href="shop.html">Shop</a>
            <a href="optimization.html">Optimization</a>
            <a href="intel.html">Intel Hub</a>
            <a href="https://merch.hopes-and-dreams.ca" target="_blank" rel="noopener noreferrer">Merch</a>
            <a href="about.html">About</a>
            <a href="privacy.html">Privacy</a>
        </nav>"""
        
    # Version explicitly highlighting the Intel Hub page
    intel_nav = standard_nav.replace('href="intel.html"', 'class="active" href="intel.html"')
    # Version explicitly highlighting the About page
    about_nav = standard_nav.replace('href="about.html"', 'class="active" href="about.html"')
    # Version explicitly highlighting the Optimization page
    opt_nav = standard_nav.replace('href="optimization.html"', 'class="active" href="optimization.html"')
    # Version explicitly highlighting the Procurement/Shop page
    shop_nav = standard_nav.replace('href="shop.html"', 'class="active" href="shop.html"')
    # Version explicitly highlighting the Privacy page
    privacy_nav = standard_nav.replace('href="privacy.html"', 'class="active" href="privacy.html"')

    for filename in html_files:
        if filename == '404.html' or filename.startswith('google'):
            continue
            
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Target the appropriate navigation block variant based on the page identity
        target_nav = standard_nav
        if filename == 'intel.html': target_nav = intel_nav
        elif filename == 'about.html': target_nav = about_nav
        elif filename == 'optimization.html': target_nav = opt_nav
        elif filename == 'shop.html': target_nav = shop_nav
        elif filename == 'privacy.html': target_nav = privacy_nav
        
        # Surgically swap out the old nav container for the streamlined version
        if re.search(r'<nav>.*?</nav>', content, re.DOTALL):
            content = re.sub(r'<nav>.*?</nav>', target_nav, content, flags=re.DOTALL)
            
        # Refresh the footer data at the same time
        if re.search(r'<footer>.*?</footer>', content, re.DOTALL):
            content = re.sub(r'<footer>.*?</footer>', NEW_FOOTER, content, flags=re.DOTALL)
            
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[SUCCESS] Re-architected menu layout inside: {filename}")
        modified_count += 1
            
    print(f"\nMainframe re-labeled. Total layout nodes polished: {modified_count}")

if __name__ == '__main__':
    sync_clean_nav()