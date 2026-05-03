import os
from dotenv import load_dotenv

def seal_static_files():
    """
    Replaces the {{WEBSITE_API_KEY}} placeholder in all HTML files
    with the actual WEBSITE_API_KEY from the .env file.
    """
    # Load the environment variables from the .env file
    load_dotenv()
    api_key = os.getenv("WEBSITE_API_KEY")
    
    if not api_key:
        print("ERROR: WEBSITE_API_KEY not found in .env file.")
        return

    # Print a safe confirmation (only shows the first 4 characters of the key)
    print(f"Sealing Syndicate static assets with API Key (starting with {api_key[:4]}...)...")

    # 1. Target all HTML files in the main root directory
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    # 2. Add all HTML files in the 'articles' directory if it exists
    if os.path.exists('articles'):
        html_files += [os.path.join('articles', f) for f in os.listdir('articles') if f.endswith('.html')]

    count = 0
    sealed_files = []

    # Loop through and process each file
    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Only rewrite the file if the placeholder actually exists inside it
            if '{{WEBSITE_API_KEY}}' in content:
                new_content = content.replace('{{WEBSITE_API_KEY}}', api_key)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"  [+] Sealed: {filepath}")
                sealed_files.append(filepath)
                count += 1
                
        except Exception as e:
            print(f"  [!] Error processing {filepath}: {e}")

    print(f"\nSeal complete. {count} files updated.")
    print("-" * 50)
    print("WARNING: Your API key is now in the static HTML files.")
    print("To prevent Git from tracking these injected files, run this command:")
    
    # Generate the exact git command for the user to copy/paste
    if sealed_files:
        git_command = "git update-index --assume-unchanged " + " ".join(sealed_files)
        print(f"\n{git_command}\n")

if __name__ == "__main__":
    seal_static_files()