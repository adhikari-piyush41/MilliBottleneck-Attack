import os
import json
import requests

# Define the output file path
output_dir = "..\Documents"
output_file = os.path.join(output_dir, "scdf_endpoints.json")

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

response = requests.get("http://localhost:9393/v3/api-docs")
api_docs = response.json()

# Extract all APIs (GET, POST, PUT, DELETE)
endpoints = []
for path, methods in api_docs['paths'].items():
    for method, details in methods.items():
        if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
            endpoints.append({
                "method": method.upper(),
                "path": path,
            })

# Save to a file
with open(output_file, "w") as file:
    json.dump(endpoints, file, indent=4)

print(f"Collected {len(endpoints)} endpoints and saved to {output_file}.")
