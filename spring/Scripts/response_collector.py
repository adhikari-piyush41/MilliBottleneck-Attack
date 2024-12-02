import subprocess
import json
import random
import string
from faker import Faker
import tempfile
import os, csv
import urllib.parse

# Initialize Faker to generate fake data
fake = Faker()

def generate_fake_data(param_type=None):
    """
    Generates fake data based on the parameter type.
    """
    if param_type == "string":
        return fake.word()  # Generates a random string
    elif param_type == "integer":
        return random.randint(1, 70000)  # Generates a random integer
    elif param_type == "boolean":
        return random.choice([True, False])  # Generates a random boolean
    elif param_type == "array":
        return [fake.word() for _ in range(random.randint(1, 5))]  # Generates a random array of strings
    else:
        # If type is absent or unrecognized, return a default random string
        return fake.word()

    
def generate_request_data(path, method, parameters):
    """
    Generates the correct request data for GET, POST, PUT requests based on the API path, method, and parameters.
    """
    # Separate path and body data
    path_params = {}
    body_params = {}
    query_params = []

    # Process the parameters and divide them into path, query, and body
    for param in parameters:
        param_type = param.get('schema', {}).get('type', None)  # Get the type safely

        if param['in'] == 'path':
            # Path parameters should be replaced in the path
            path_params[param['name']] = generate_fake_data(param_type)
        elif param['in'] == 'query':
            # Query parameters will be added to the URL
            query_params.append(f"{param['name']}={generate_fake_data(param_type)}")
        elif param['in'] == 'body':
            # Body parameters will go into the body for POST/PUT requests
            body_params[param['name']] = generate_fake_data(param_type)

    # Replace path parameters in the URL
    for key, value in path_params.items():
        path = path.replace(f"{{{key}}}", str(value))

    # Construct the full URL with query parameters
    if query_params:
        url = f"{path}?" + "&".join(query_params)
    else:
        url = urllib.parse.quote(path)

    return url, body_params

def execute_ab_request(url, body_params, method, csv_file="./Documents/ab_results.csv"):
    """
    Executes the Apache Benchmark (ab) command and collects the response time, saving results to a CSV file.
    """
    # If the CSV file doesn't exist, create it and add the headers
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write header row with fixed and dynamic columns
            writer.writerow(["URL", "Failed Requests", "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%"])
    
    cmd = ""
    temp_file_path = None

    # If method is POST or PUT, we need to include the body
    if method in ["POST", "PUT"]:
        # Prepare the data in JSON format
        body_data = json.dumps(body_params)

        # Create a temporary file to store the body data
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_file:
            temp_file.write(body_data)
            temp_file_path = temp_file.name  # Get the file path

        # Construct the ab command with the temporary file as POST/PUT data
        if method == "POST":
            cmd = f"ab -n 7000 -c 50 -p {temp_file_path} -T 'application/json' {url}"
        else:
            cmd = f"ab -n 7000 -c 50 -u {temp_file_path} -T 'application/json' {url}"
    else:
        # For GET and DELETE, no body is needed
        cmd = f"ab -n 7000 -c 50 {url}"

    try:
        # Execute the command
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        output = result.decode('utf-8')

        # Parse ab output for required metrics
        failed_requests = 0
        response_times = {
            "50%": None,
            "66%": None,
            "75%": None,
            "80%": None,
            "90%": None,
            "95%": None,
            "98%": None,
            "99%": None,
            "100%": None,
        }

        # Extract failed requests
        failed_requests_line = next((line for line in output.splitlines() if "Failed requests" in line), None)
        if failed_requests_line:
            failed_requests = int(failed_requests_line.split(":")[1].strip())

        # Extract response time percentages
        percentage_section = next((line for line in output.splitlines() if "Percentage of the requests served within a certain time" in line), None)
        if percentage_section:
            percentage_lines = output.splitlines()[output.splitlines().index(percentage_section) + 1:]
            for line in percentage_lines:
                parts = line.split("%")
                if len(parts) == 2:
                    percentage = parts[0].strip()
                    time_ms = parts[1].strip().split()[0]  # Extract only the time value
                    if percentage + "%" in response_times:
                        response_times[percentage + "%"] = time_ms

        # Save results to CSV
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                url,
                failed_requests,
                response_times["50%"],
                response_times["66%"],
                response_times["75%"],
                response_times["80%"],
                response_times["90%"],
                response_times["95%"],
                response_times["98%"],
                response_times["99%"],
                response_times["100%"]
            ])
        # print(f"Results saved to {csv_file}")

    except subprocess.CalledProcessError as e:
        print("---------------------------------------------------------")
        print(f"[Error: ] Cannot execute ab: {e.output.decode('utf-8')}")
        print(f"[Debug: ] ab Command failed: {cmd}")
        print("---------------------------------------------------------")
    finally:
        # Clean up the temporary file if it was created
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def send_ab_requests_from_api_spec(api_spec, verbose=True):
    """
    Loops through the OpenAPI specification and sends requests using ab for each endpoint.
    """
    for path, methods in api_spec['paths'].items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                if verbose:
                    print(f"[Verbose: ] Processing {method.upper()} request for {path}...")
                # Prepare the request data (URL and body)
                url, body_params = generate_request_data(path, method, details.get('parameters', []))
                url = f"http://localhost:9393{url}"
                
                # Execute the ab request
                execute_ab_request(url, body_params, method.upper())



file_path = "./Documents/scdf_endpoints.json"
with open(file_path, 'r') as file:
    # Load the JSON content into a Python dictionary
    api_spec = json.load(file)


# Call the function to send ab requests
send_ab_requests_from_api_spec(api_spec)
