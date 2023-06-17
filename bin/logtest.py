import pandas as pd
import re

# Define regex pattern for the log line
pattern = re.compile(r'level=(\w+)\s+contentType="([^"]+)"\s+url="([^"]+)"')

# Open log file
with open('./logs/repo-oceanscape-loaded-2023-06-09-13-15-33.log', 'r') as f:
    log_data = f.readlines()

# Parse logs
parsed_data = []
for line in log_data:
    match = pattern.search(line)
    if match:
        data = {
            'level': match.group(1),
            'contentType': match.group(2),
            'url': match.group(3)
        }
        parsed_data.append(data)

# Store data in pandas DataFrame
df = pd.DataFrame(parsed_data)

# Print DataFrame
print(df)
