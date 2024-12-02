import subprocess
import json
import random
import string
from faker import Faker
import tempfile
import os, csv
import urllib.parse
import psutil
import time

HOST = "http://localhost:9393"
API_SPEC_FILE = "./Documents/scdf_endpoints.json"
RESULTS_FILE = "./Documents/1_benign_response_time.csv"

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

# def execute_ab_request(url, body_params, method, csv_file="./Documents/benign_response_time.csv"):
#     """
#     Executes the Apache Benchmark (ab) command and collects the response time, saving results to a CSV file.
#     """
#     # If the CSV file doesn't exist, create it and add the headers
#     if not os.path.exists(csv_file):
#         with open(csv_file, mode='w', newline='') as file:
#             writer = csv.writer(file)
#             # Write header row with fixed and dynamic columns
#             writer.writerow(["URL", "Failed Requests", "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%"])
    
#     cmd = ""
#     temp_file_path = None

#     # If method is POST or PUT, we need to include the body
#     if method in ["POST", "PUT"]:
#         # Prepare the data in JSON format
#         body_data = json.dumps(body_params)

#         # Create a temporary file to store the body data
#         with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_file:
#             temp_file.write(body_data)
#             temp_file_path = temp_file.name  # Get the file path

#         # Construct the ab command with the temporary file as POST/PUT data
#         if method == "POST":
#             cmd = f"ab -n 7000 -c 50 -p {temp_file_path} -T 'application/json' {url}"
#         else:
#             cmd = f"ab -n 7000 -c 50 -u {temp_file_path} -T 'application/json' {url}"
#     else:
#         # For GET and DELETE, no body is needed
#         cmd = f"ab -n 7000 -c 50 {url}"

#     try:
#         # Execute the command
#         result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
#         output = result.decode('utf-8')

#         # Parse ab output for required metrics
#         failed_requests = 0
#         response_times = {
#             "50%": None,
#             "66%": None,
#             "75%": None,
#             "80%": None,
#             "90%": None,
#             "95%": None,
#             "98%": None,
#             "99%": None,
#             "100%": None,
#         }

#         # Extract failed requests
#         failed_requests_line = next((line for line in output.splitlines() if "Failed requests" in line), None)
#         if failed_requests_line:
#             failed_requests = int(failed_requests_line.split(":")[1].strip())

#         # Extract response time percentages
#         percentage_section = next((line for line in output.splitlines() if "Percentage of the requests served within a certain time" in line), None)
#         if percentage_section:
#             percentage_lines = output.splitlines()[output.splitlines().index(percentage_section) + 1:]
#             for line in percentage_lines:
#                 parts = line.split("%")
#                 if len(parts) == 2:
#                     percentage = parts[0].strip()
#                     time_ms = parts[1].strip().split()[0]  # Extract only the time value
#                     if percentage + "%" in response_times:
#                         response_times[percentage + "%"] = time_ms

#         # Save results to CSV
#         with open(csv_file, mode='a', newline='') as file:
#             writer = csv.writer(file)
#             writer.writerow([
#                 url,
#                 failed_requests,
#                 response_times["50%"],
#                 response_times["66%"],
#                 response_times["75%"],
#                 response_times["80%"],
#                 response_times["90%"],
#                 response_times["95%"],
#                 response_times["98%"],
#                 response_times["99%"],
#                 response_times["100%"]
#             ])
#         # print(f"Results saved to {csv_file}")

#     except subprocess.CalledProcessError as e:
#         print("---------------------------------------------------------")
#         print(f"[Error: ] Cannot execute ab: {e.output.decode('utf-8')}")
#         print(f"[Debug: ] ab Command failed: {cmd}")
#         print("---------------------------------------------------------")
#     finally:
#         # Clean up the temporary file if it was created
#         if temp_file_path and os.path.exists(temp_file_path):
#             os.remove(temp_file_path)
# def execute_ab_request(url, body_params, method, csv_file="./Documents/2_benign_response_time.csv"):
    # """
    # Executes the Apache Benchmark (ab) command and collects the response time, saving results to a CSV file.
    # """
    # def calculate_pmb(ab_result: str) -> tuple[float, float, int]:
    #     """
    #     Calculate the percentile millibottleneck (PMB) for requests above a threshold.
    #     Args:
    #         ab_result (str): The Apache Bench output.
    #     Returns:
    #         tuple: PMB, total PMB time, and the count of requests over the threshold.
    #     """
    #     bottleneck_threshold = 500
        
    #     for line in ab_result.splitlines():
    #         if "Time per request" in line and "(mean, across all" not in line:

    #             try:
    #                 bottleneck_request_time = float(line.split()[3])
    #                 if bottleneck_request_time < bottleneck_threshold:
    #                     return bottleneck_request_time
    #                 else:
    #                     return 0
    #             except ValueError:
    #                 continue


    # # If the CSV file doesn't exist, create it and add the headers
    # if not os.path.exists(csv_file):
    #     with open(csv_file, mode='w', newline='') as file:
    #         writer = csv.writer(file)
    #         # Write header row with fixed and dynamic columns
    #         writer.writerow(["URL", "Failed Requests", "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%", "bottleneck_request_time"])
    
    # cmd = ""
    # temp_file_path = None

    # # If method is POST or PUT, we need to include the body
    # if method in ["POST", "PUT"]:
    #     # Prepare the data in JSON format
    #     body_data = json.dumps(body_params)

    #     # Create a temporary file to store the body data
    #     with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_file:
    #         temp_file.write(body_data)
    #         temp_file_path = temp_file.name  # Get the file path

    #     # Construct the ab command with the temporary file as POST/PUT data
    #     if method == "POST":
    #         cmd = f"ab -n 7000 -c 30 -p {temp_file_path} -T 'application/json' {url}"
    #     else:
    #         cmd = f"ab -n 7000 -c 30 -u {temp_file_path} -T 'application/json' {url}"
    # else:
    #     # For GET and DELETE, no body is needed
    #     cmd = f"ab -n 7000 -c 30 {url}"

    # try:
    #     # Execute the command
    #     result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    #     output = result.decode('utf-8')
    #     bottleneck_request_time = calculate_pmb(output)


    #     # Parse ab output for required metrics
    #     failed_requests = 0
    #     response_times = {
    #         "50%": None,
    #         "66%": None,
    #         "75%": None,
    #         "80%": None,
    #         "90%": None,
    #         "95%": None,
    #         "98%": None,
    #         "99%": None,
    #         "100%": None,
    #     }

    #     # Extract failed requests
    #     failed_requests_line = next((line for line in output.splitlines() if "Failed requests" in line), None)
    #     if failed_requests_line:
    #         failed_requests = int(failed_requests_line.split(":")[1].strip())

    #     # Extract response time percentages
    #     percentage_section = next((line for line in output.splitlines() if "Percentage of the requests served within a certain time" in line), None)
    #     if percentage_section:
    #         percentage_lines = output.splitlines()[output.splitlines().index(percentage_section) + 1:]
    #         for line in percentage_lines:
    #             parts = line.split("%")
    #             if len(parts) == 2:
    #                 percentage = parts[0].strip()
    #                 time_ms = parts[1].strip().split()[0]  # Extract only the time value
    #                 if percentage + "%" in response_times:
    #                     response_times[percentage + "%"] = time_ms

    #     # Save results to CSV
    #     with open(csv_file, mode='a', newline='') as file:
    #         writer = csv.writer(file)
    #         writer.writerow([
    #             url,
    #             failed_requests,
    #             response_times["50%"],
    #             response_times["66%"],
    #             response_times["75%"],
    #             response_times["80%"],
    #             response_times["90%"],
    #             response_times["95%"],
    #             response_times["98%"],
    #             response_times["99%"],
    #             response_times["100%"],
    #             bottleneck_request_time
    #         ])

    # except subprocess.CalledProcessError as e:
    #     print("---------------------------------------------------------")
    #     print(f"[Error] Cannot execute ab")
    #     print(f"[Debug] ab Command failed: {cmd}")
    #     print("---------------------------------------------------------")
    # finally:
    #     # Clean up the temporary file if it was created
    #     if temp_file_path and os.path.exists(temp_file_path):
    #         os.remove(temp_file_path)



def execute_ab_request(url, body_params, method, csv_file="./Documents/1_benign_response_time.csv"):
    """
    Executes the Apache Benchmark (ab) command and collects the response time, network, and memory usage, saving results to a CSV file.
    """
    def calculate_pmb(ab_result: str) -> float:
        """
        Calculate the percentile millibottleneck (PMB) for requests above a threshold.
        Args:
            ab_result (str): The Apache Bench output.
        Returns:
            float: PMB value for the threshold.
        """
        bottleneck_threshold = 500
        for line in ab_result.splitlines():
            if "Time per request" in line and "(mean, across all" not in line:
                try:
                    bottleneck_request_time = float(line.split()[3])
                    return bottleneck_request_time if bottleneck_request_time <= bottleneck_threshold else 0.0
                except ValueError:
                    continue
        return None    

    cmd = ""
    temp_file_path = None

    # If method is POST or PUT, we need to include the body
    if method in ["POST", "PUT"]:
        body_data = json.dumps(body_params)
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_file:
            temp_file.write(body_data)
            temp_file_path = temp_file.name
        if method == "POST":
            cmd = f"ab -n 7000 -c 20 -p {temp_file_path} -T 'application/json' {url}"
        else:
            cmd = f"ab -n 7000 -c 20 -u {temp_file_path} -T 'application/json' {url}"
    else:
        cmd = f"ab -n 7000 -c 20 {url}"

    try:
        # Track network and memory usage
        network_start = psutil.net_io_counters()
        memory_usage = []
        start_time = time.time()

        # Monitor in a separate thread
        def monitor_resource_usage():
            while True:
                memory_usage.append(psutil.virtual_memory().percent)
                time.sleep(0.1)

        import threading
        monitor_thread = threading.Thread(target=monitor_resource_usage, daemon=True)
        monitor_thread.start()

        # Execute the command
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        output = result.decode('utf-8')

        # Stop monitoring
        elapsed_time = time.time() - start_time
        monitor_thread.join(timeout=0)
        network_end = psutil.net_io_counters()

        # Calculate network and memory usage
        total_network_usage = (network_end.bytes_sent + network_end.bytes_recv) - (network_start.bytes_sent + network_start.bytes_recv)
        avg_network_usage_kbps = (total_network_usage / elapsed_time) / 1024
        avg_memory_usage_mb = sum(memory_usage) / len(memory_usage) if memory_usage else 0

        # Extract metrics from ab output
        bottleneck_request_time = calculate_pmb(output)
        failed_requests = 0
        response_times = {key: None for key in ["50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%"]}
        failed_requests_line = next((line for line in output.splitlines() if "Failed requests" in line), None)
        if failed_requests_line:
            failed_requests = int(failed_requests_line.split(":")[1].strip())
        percentage_section = next((line for line in output.splitlines() if "Percentage of the requests served within a certain time" in line), None)
        if percentage_section:
            percentage_lines = output.splitlines()[output.splitlines().index(percentage_section) + 1:]
            for line in percentage_lines:
                parts = line.split("%")
                if len(parts) == 2:
                    percentage = parts[0].strip()
                    time_ms = parts[1].strip().split()[0]
                    if percentage + "%" in response_times:
                        response_times[percentage + "%"] = time_ms

        # Save results to CSV
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                url,
                failed_requests,
                response_times["50%"], response_times["66%"], response_times["75%"], response_times["80%"],
                response_times["90%"], response_times["95%"], response_times["98%"], response_times["99%"],
                response_times["100%"], bottleneck_request_time, avg_memory_usage_mb, avg_network_usage_kbps
            ])

    except subprocess.CalledProcessError as e:
        print("---------------------------------------------------------")
        print(f"[Error] Cannot execute ab")
        print(f"[Debug] ab Command failed: {cmd}")
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
                url = f"{HOST}{url}"
                
                # Execute the ab request
                execute_ab_request(url, body_params, method.upper())





with open(RESULTS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header row with fixed and dynamic columns
        writer.writerow([
            "URL", "Failed Requests", "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%",
            "bottleneck_request_time", "avg_memory_usage_mb", "avg_network_usage_kbps"
        ])

with open(API_SPEC_FILE, 'r') as file:
    # Load the JSON content into a Python dictionary
    api_spec = json.load(file)


# Call the function to send ab requests
send_ab_requests_from_api_spec(api_spec)
