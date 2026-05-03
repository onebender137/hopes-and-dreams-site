import os
import re
from dotenv import load_dotenv

def seal_static_files():
    """
    Replaces the {{WEBSITE_API_KEY}} placeholder in all HTML files
    with the actual WEBSITE_API_KEY from the .env file.
    """
    load_dotenv()
    api_key = os.getenv("WEBSITE_API_KEY")

    if not api_key:
        print("ERROR: WEBSITE_API_KEY not found in .env file.")
        return

    print(f"Sealing Syndicate static assets with API Key (starting with {api_key[:4]}...)...")

    # Target all HTML files in root and articles/
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    if os.path.exists('articles'):
        html_files += [os.path.join('articles', f) for f in os.listdir('articles') if f.endswith('.html')]

    count = 0
    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if '{{WEBSITE_API_KEY}}' in content:
                new_content = content.replace('{{WEBSITE_API_KEY}}', api_key)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"  [+] Sealed: {filepath}")
                count += 1
        except Exception as e:
            print(f"  [!] Error processing {filepath}: {e}")

    print(f"\nSeal complete. {count} files updated.")
    print("WARNING: Your API key is now in the static HTML files. Do not commit these changes if you want to keep the key private in the repository.")

if __name__ == "__main__":
    seal_static_files()
