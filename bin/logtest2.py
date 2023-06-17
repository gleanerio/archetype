# parse_log.py
import re
import pandas as pd

with open('./logs/repo-oceanscape-loaded-2023-06-09-13-15-33.log', 'r') as f:
    log_lines = [line.strip() for line in f.readlines()]

# Regular expression pattern to capture level, contentType, and url
# pattern = r'level=(\w+) contentType="(.*?)"] url="(.*?)"'
pattern = re.compile(r'level=(\w+)\s+contentType="([^"]+)"\s+url="([^"]+)"')

parsed_data = []

for line in log_lines:
    match = re.search(pattern, line)
    if match:
        level, content_type, url = match.groups()
        parsed_data.append({'level': level, 'contentType': content_type, 'url': url})

# Create the pandas DataFrame
df = pd.DataFrame(parsed_data)

print(df)