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


# To store the endpoints
endpoints = []

# Iterate through the paths and methods to collect GET, POST, PUT, DELETE information
for path, methods in api_docs['paths'].items():
    for method, details in methods.items():
        if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
            # Prepare basic endpoint info
            endpoint_info = {
                "method": method.upper(),
                "path": path,
                "parameters": []
            }
            
            
            if "parameters" in details:
                for param in details["parameters"]:
                    # Check if 'in' exists to avoid KeyError
                    if "in" in param:
                        # Handle query parameters
                        if param["in"] == "query":
                            param_info = {"name": param["name"], "in": param["in"]}
                            
                            # Check if 'schema' and 'type' are present in the parameter
                            if "schema" in param and "type" in param["schema"]:
                                param_info["type"] = param["schema"]["type"]
                            else:
                                # If 'type' is not present, set a default or log the issue
                                param_info["type"] = "unknown"  # or you can skip this parameter or log a warning
                            
                            # Add the parameter to the list
                            endpoint_info["parameters"].append(param_info)

            # Collect body data for POST and PUT methods (if available)
            # if method.upper() in ["POST", "PUT"] and "requestBody" in details:
            #     body_params = details["requestBody"]["content"]["application/json"]["schema"]["additionalProperties"]
            #     endpoint_info["body"] = {}
            #     for k, v in body_params.items():
            #         if isinstance(v, dict) and "type" in v:
            #             endpoint_info["body"][k] = v["type"]
            #         else:
            #             # Handle cases where v is not a dictionary or does not contain the 'type' key
            #             print(f"Warning: Skipping '{k}' because it does not have a valid type definition or is not a dictionary.")

            
            # endpoints.append(endpoint_info)

            if method.upper() in ["POST", "PUT"] and "requestBody" in details:
                # Check if the schema exists for the requestBody
                if "content" in details["requestBody"] and "application/json" in details["requestBody"]["content"]:
                    schema = details["requestBody"]["content"]["application/json"].get("schema", {})

                    # If schema exists, proceed to extract additionalProperties if present
                    if "additionalProperties" in schema:
                        body_params = schema["additionalProperties"]
                        endpoint_info["body"] = {}

                        for k, v in body_params.items():
                            if isinstance(v, dict) and "type" in v:
                                endpoint_info["body"][k] = v["type"]
                            else:
                                # Handle cases where v is not a dictionary or does not contain the 'type' key
                                print(f"Warning: Skipping '{k}' because it does not have a valid type definition or is not a dictionary.")
                    else:
                        print(f"Warning: No additionalProperties found in schema for {path} [{method}]")
                else:
                    print(f"Warning: No valid content for 'application/json' in requestBody for {path} [{method}]")
                
            endpoints.append(endpoint_info)


# Save to a file
with open(output_file, "w") as file:
    json.dump(endpoints, file, indent=4)

print(f"Collected {len(endpoints)} endpoints and saved to {output_file}.")
