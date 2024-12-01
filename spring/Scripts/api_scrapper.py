import requests
import json

# Fetch OpenAPI documentation
response = requests.get("http://localhost:9393/v3/api-docs")
api_docs = response.json()