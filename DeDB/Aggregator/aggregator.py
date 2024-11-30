from zellular import Zellular, get_operators
import requests
import base64
import time
import json

# Zellular and Operator Configuration
APP_NAME = "avs-downtime-monitor"
OPERATORS = get_operators()  # Fetch the list of operators dynamically
BASE_URLS = [op["socket"] for op in OPERATORS.values() if "socket" in op]
zellular = Zellular(APP_NAME, BASE_URLS[0])

THRESHOLD = 2  # Minimum number of valid signatures required


# Query a node's status
def query_node_status(node_url):
    try:
        response = requests.get(f"{node_url}/status")
        return response.json()
    except Exception as e:
        return {"node_id": node_url, "status": "down", "timestamp": int(time.time())}


# Collect signed responses from operators
def collect_signatures(target_node_url):
    signatures = []
    for operator_url in BASE_URLS:
        if operator_url != target_node_url:
            try:
                response = requests.post(
                    f"{operator_url}/check_node",
                    json={"node_url": target_node_url}
                )
                if response.status_code == 200:
                    signatures.append(response.json())
            except Exception as e:
                print(f"Error collecting signature from {operator_url}: {e}")
    return signatures


# Submit events to the sequencer
def submit_to_sequencer(event):
    try:
        response = zellular.send([event])
        if response.status_code == 200:
            print("Event submitted successfully to the sequencer.")
        else:
            print(f"Failed to submit event: {response.text}")
    except Exception as e:
        print(f"Error submitting event to sequencer: {e}")


if __name__ == "__main__":
    while True:
        for operator_url in BASE_URLS:
            target_status = query_node_status(operator_url)
            if target_status["status"] == "down":
                signatures = collect_signatures(operator_url)
                if len(signatures) >= THRESHOLD:
                    downtime_event = {
                        "node_id": target_status["node_id"],
                        "status": "down",
                        "timestamp": target_status["timestamp"],
                        "proofs": signatures
                    }
                    submit_to_sequencer(downtime_event)
        time.sleep(30)
