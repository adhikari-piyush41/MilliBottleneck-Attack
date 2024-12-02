import json, csv
from faker import Faker
from helper import generate_request_data, execute_ab_request

# GLOBAL CONSTANTS
HOST = "http://localhost:9393"
MICROSERVICE = "spring"
API_SPEC_FILE = f"./{MICROSERVICE}/documents/scdf_endpoints.json"
RESULTS_FILE = f"./results/{MICROSERVICE}_benign_results.csv"
DEBUG = True
BOTTLENECK_THRESHOLD = 500 # milliseconds
N_REQUESTS = 7000
N_CONCURRENCY = 20


def send_ab_requests_from_api_spec(api_spec, verbose=True):
    """
    Loops through the OpenAPI specification and sends requests using ab for each endpoint.
    """
    # Initialize Faker to generate fake data
    fake = Faker()
    for path, methods in api_spec['paths'].items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                if verbose:
                    print(f"[Verbose: ] Processing {method.upper()} request for {path}...")
                # Prepare the request data (URL and body)
                url, body_params = generate_request_data(path, method, details.get('parameters', []), fake)
                # url = f"{HOST}{url}"
                
                # Execute the ab request
                execute_ab_request(host=HOST, url=url, body_params=body_params, method=method.upper(), csv_file=RESULTS_FILE, n_requests=N_REQUESTS, n_concurrency=N_CONCURRENCY, bottleneck_threshold=BOTTLENECK_THRESHOLD)



with open(RESULTS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header row with fixed and dynamic columns
        writer.writerow([
            "URL", "Failed Requests", "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "100%",
            "Bottleneck Length", "Average Memory Usage (MB)", "Average Network Usage (MBps)"
        ])

with open(API_SPEC_FILE, 'r') as file:
    # Load the JSON content into a Python dictionary
    api_spec = json.load(file)


# Call the function to send ab requests
send_ab_requests_from_api_spec(api_spec, DEBUG)
