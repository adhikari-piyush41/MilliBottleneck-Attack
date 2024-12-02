import subprocess
import time
from typing import List

# Global Constants and Variables
ENDPOINTS = {
    "login": "http://172.18.16.1/login",
    "catalogue": "http://172.18.16.1/catalogue",
    "cart": "http://172.18.16.1/cart",
    "update": "http://172.18.16.1/cart",
    "orders": "http://172.18.16.1/orders",
    "customers": "http://172.18.16.1/customers/1",
    "cards": "http://172.18.16.1/cards",
    "register": "http://172.18.16.1/register",
}

TOTAL_REQUESTS = 7000
CONCURRENCY = 10
THRESHOLD = 500
REST_DURATION = 1
LONG_OFF_DURATION = 5

OUTPUT_FILE = "latency_results.txt"
DOCKER_STATS_FILE = "docker_memory_usage.txt"
PMB_FILE = "pmb_results.txt"
GLOBAL_PMB_FILE = "global_pmb_results.txt"

# Global PMB tracking
TOTAL_PMB_TIME = 0
TOTAL_REQUESTS_OVER_THRESHOLD = 0


def run_command(command: List[str]) -> str:
    """
    Run a shell command and return its output.
    Args:
        command (List[str]): The command to run as a list of strings.
    Returns:
        str: The output of the command.
    """
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return e.output


def run_ab_test(endpoint_name: str, endpoint_url: str) -> None:
    """
    Run Apache Bench (ab) test for a given endpoint and calculate PMB.
    Args:
        endpoint_name (str): Name of the endpoint.
        endpoint_url (str): URL of the endpoint.
    """
    global TOTAL_PMB_TIME, TOTAL_REQUESTS_OVER_THRESHOLD

    print(f"Testing endpoint: {endpoint_name} ({endpoint_url})")

    # Run Apache Bench (ab) and capture the output
    ab_command = ["ab", "-n", str(TOTAL_REQUESTS), "-c", str(CONCURRENCY), endpoint_url]
    ab_result = run_command(ab_command)

    # Extract 95th and 99th percentile latencies
    p95 = extract_percentile_latency(ab_result, "95%")
    p99 = extract_percentile_latency(ab_result, "99%")

    # Process response times to calculate PMB
    pmb, total_pmb_time, requests_over_threshold = calculate_pmb(ab_result)

    # Update global PMB tracking
    TOTAL_PMB_TIME += total_pmb_time
    TOTAL_REQUESTS_OVER_THRESHOLD += requests_over_threshold

    # Write results to files
    write_results(endpoint_name, p95, p99, pmb, total_pmb_time, requests_over_threshold)


def extract_percentile_latency(ab_result: str, percentile: str) -> float:
    """
    Extract latency for a given percentile from Apache Bench output.
    Args:
        ab_result (str): The Apache Bench output.
        percentile (str): The percentile to extract (e.g., "95%", "99%").
    Returns:
        float: The extracted latency.
    """
    try:
        for line in ab_result.splitlines():
            if percentile in line:
                return float(line.split()[1])
    except ValueError:
        print(f"Failed to parse {percentile} latency.")
    return 0.0


def calculate_pmb(ab_result: str) -> tuple[float, float, int]:
    """
    Calculate the percentile millibottleneck (PMB) for requests above a threshold.
    Args:
        ab_result (str): The Apache Bench output.
    Returns:
        tuple: PMB, total PMB time, and the count of requests over the threshold.
    """
    total_pmb_time = 0.0
    requests_over_threshold = 0

    for line in ab_result.splitlines():
        if "Time per request" in line and "(mean, across all" not in line:
            try:
                request_time = float(line.split()[3])
                if request_time > THRESHOLD:
                    total_pmb_time += request_time
                    requests_over_threshold += 1
            except ValueError:
                continue

    pmb = (total_pmb_time / requests_over_threshold) if requests_over_threshold > 0 else 0.0
    return pmb, total_pmb_time, requests_over_threshold


def write_results(endpoint_name: str, p95: float, p99: float, pmb: float, total_pmb_time: float,
                  requests_over_threshold: int) -> None:
    """
    Write the latency and PMB results to their respective files.
    Args:
        endpoint_name (str): Name of the endpoint.
        p95 (float): 95th percentile latency.
        p99 (float): 99th percentile latency.
        pmb (float): Percentile millibottleneck.
        total_pmb_time (float): Total PMB time.
        requests_over_threshold (int): Count of requests over the threshold.
    """
    with open(OUTPUT_FILE, 'a') as f:
        f.write(f"Endpoint: {endpoint_name}\n")
        f.write(f"95th percentile latency: {p95}ms\n")
        f.write(f"99th percentile latency: {p99}ms\n")
        f.write("----------------------------------------\n")

    with open(PMB_FILE, 'a') as f:
        f.write(f"Endpoint: {endpoint_name}\n")
        f.write(f"PMB: {pmb} ms (threshold: {THRESHOLD} ms)\n")
        f.write(f"Requests over threshold: {requests_over_threshold}\n")
        f.write(f"----------------------------------------\n")


def capture_docker_stats() -> None:
    """
    Capture Docker memory usage stats and write to a file.
    """
    print("Capturing Docker stats...")
    docker_command = ["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.MemUsage}}"]
    stats = run_command(docker_command)

    with open(DOCKER_STATS_FILE, 'w') as f:
        f.write(stats)

    print("Docker memory usage (top containers):")
    print(stats)


def main():
    """
    Main function to coordinate attack simulation and monitoring.
    """
    # Clean old results
    for file in [OUTPUT_FILE, DOCKER_STATS_FILE, PMB_FILE, GLOBAL_PMB_FILE]:
        open(file, 'w').close()

    for cycle in range(2):  # Number of cycles
        print(f"Starting cycle {cycle + 1}...")

        # Run tests for each endpoint
        for endpoint_name, endpoint_url in ENDPOINTS.items():
            run_ab_test(endpoint_name, endpoint_url)
            time.sleep(REST_DURATION)

        # Long OFF period
        print(f"Resting for {LONG_OFF_DURATION} seconds...")
        time.sleep(LONG_OFF_DURATION)

    # Write global PMB results
    avg_pmb = (TOTAL_PMB_TIME / TOTAL_REQUESTS_OVER_THRESHOLD) if TOTAL_REQUESTS_OVER_THRESHOLD > 0 else 0.0
    with open(GLOBAL_PMB_FILE, 'a') as f:
        f.write(f"Global Average PMB: {avg_pmb} ms\n")
        f.write(f"Total PMB time: {TOTAL_PMB_TIME} ms\n")
        f.write(f"Total requests exceeding threshold: {TOTAL_REQUESTS_OVER_THRESHOLD}\n")

    # Capture Docker stats after testing
    capture_docker_stats()


if __name__ == "__main__":
    main()
