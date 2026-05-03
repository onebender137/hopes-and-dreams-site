import re
import json
import os

def migrate_transmissions():
    transmissions_file = "transmissions.html"
    json_file = "transmissions.json"

    if not os.path.exists(transmissions_file):
        print(f"Error: {transmissions_file} not found.")
        return

    with open(transmissions_file, "r") as f:
        html = f.read()

    # Regex to find archive items
    # Example: <a href="articles/2026-03-08-The-Neurobiology-of-Sulbutiamine.html" class="archive-item">
    #                <span class="title">The Neurobiology of Sulbutiamine</span>
    #                <span class="date">2026-03-08</span>
    #            </a>
    pattern = r'<a href="(articles/.*?)" class="archive-item">\s*<span class="title">(.*?)</span>\s*<span class="date">(.*?)</span>\s*</a>'

    items = re.findall(pattern, html, re.DOTALL)

    transmissions = []
    for href, title, date in items:
        transmissions.append({
            "href": href,
            "title": title,
            "date": date
        })

    with open(json_file, "w") as f:
        json.dump(transmissions, f, indent=4)

    print(f"Successfully migrated {len(transmissions)} items to {json_file}")

if __name__ == "__main__":
    migrate_transmissions()
