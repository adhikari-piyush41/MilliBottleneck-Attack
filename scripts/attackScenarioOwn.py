import json, csv
from faker import Faker
from helper import generate_request_data, execute_ab_request
from concurrent.futures import ThreadPoolExecutor

# GLOBAL CONSTANTS
HOST = "http://localhost:9393"
MICROSERVICE = "spring"
API_SPEC_FILE = f"./{MICROSERVICE}/documents/scdf_endpoints.json"
RESULTS_FILE = f"./results/{MICROSERVICE}_attack_results.csv"
DEBUG = True
BOTTLENECK_THRESHOLD = 0 # milliseconds
N_REQUESTS = 100
N_CONCURRENCY = 100
MAX_API_TO_ATTACK = 30


def send_ab_requests_from_api_spec(api_spec, verbose=True, max_workers=10):
    """
    Loops through the OpenAPI specification and sends requests using ab for each endpoint.
    Executes requests simultaneously, with a limit on the number of simultaneous requests.
    """
    fake = Faker()
    def process_request(path, method, details):
        """
        Inner function to process a single API request.
        """
        if verbose:
            print(f"[Verbose] Processing {method.upper()} request for {path}...")

        # Prepare the request data (URL and body)
        url, body_params = generate_request_data(path, method, details.get('parameters', []), fake)
        # url = f"http://localhost:9393{url}"

        # Execute the ab request
        execute_ab_request(host=HOST, url=url, body_params=body_params, method=method.upper(), csv_file=RESULTS_FILE, n_requests=N_REQUESTS, n_concurrency=N_CONCURRENCY, bottleneck_threshold=BOTTLENECK_THRESHOLD)

    # Collect tasks for concurrent execution
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for path, methods in api_spec['paths'].items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                    # Submit each task to the executor
                    tasks.append(executor.submit(process_request, path, method, details))

    # Optionally wait for all tasks to complete
    for task in tasks:
        task.result()  # This will raise any exception encountered in the worker thread

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
send_ab_requests_from_api_spec(api_spec, DEBUG, MAX_API_TO_ATTACK)
