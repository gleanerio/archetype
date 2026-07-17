import json
import requests
import yaml
import os
from datetime import datetime
import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def main():
    url = "https://catalogue.odis.org/odis-arch-records"
    # Determine script directory to use absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sources_path = os.path.join(script_dir, "sources.yaml")
    
    print(f"Fetching records from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        records = response.json()
    except Exception as e:
        print(f"Error fetching records: {e}")
        return

    new_sources = []
    for rec in records:
        # Mapping fields
        # ds_name_english -> propername
        # ds_url -> domain
        # odis_arch_url -> url
        # odis_arch_type -> sourcetype
        # id -> pid
        
        proper_name = rec.get("ds_name_english", "")
        name = slugify(proper_name)
        
        source_entry = {
            "name": name,
            "propername": proper_name,
            "domain": rec.get("ds_url", ""),
            "pid": f"https://catalogue.odis.org/view/{rec.get('id')}",
            "sourcetype": rec.get("odis_arch_type", "").lower(),
            "url": rec.get("odis_arch_url", ""),
            "changefreq": "daily", # Defaulting as seen in original
            "backend": "Custom",    # Defaulting
            "headless": False,      # Defaulting
            "active": True          # Defaulting
        }
        # Special case for headless if needed, but per instructions we just match fields
        if source_entry["sourcetype"] == "sitegraph":
             source_entry["headless"] = False # Matches original logic usually
        
        new_sources.append(source_entry)

    output_data = {"sources": new_sources}

    # Backup existing sources.yaml
    if os.path.exists(sources_path):
        today = datetime.now().strftime("%Y%m%d")
        backup_path = f"{sources_path}_{today}"
        print(f"Backing up {sources_path} to {backup_path}...")
        os.rename(sources_path, backup_path)

    # Write new sources.yaml
    print(f"Writing new {sources_path}...")
    with open(sources_path, 'w') as f:
        yaml.dump(output_data, f, sort_keys=False, default_flow_style=False)
    
    print("Done!")

if __name__ == "__main__":
    main()
