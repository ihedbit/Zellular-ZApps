import requests
import random
import time
import json

OPERATORS = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002"
]

SEQUENCER_URL = "http://zellular-sequencer.example.com"

def query_node_status(node_url):
    """
    Queries a node to get its current status.
    """
    try:
        response = requests.get(f"{node_url}/status")
        return response.json()
    except Exception as e:
        return {"node_id": node_url, "status": "down", "timestamp": int(time.time())}

def collect_signatures(target_node_id):
    """
    Collects signatures from other nodes about the status of a target node.
    """
    signatures = []
    for operator_url in OPERATORS:
        if operator_url != target_node_id:
            try:
                response = requests.post(
                    f"{operator_url}/update_state",
                    json={"node_id": target_node_id, "status": "down", "timestamp": int(time.time())}
                )
                if response.status_code == 200:
                    signatures.append({"node": operator_url, "sig": "sample_signature"})
            except Exception as e:
                continue
    return signatures

def submit_to_sequencer(downtime_event):
    """
    Sends the downtime event to the Zellular sequencer.
    """
    try:
        response = requests.post(SEQUENCER_URL, json=downtime_event)
        if response.status_code == 200:
            print("Downtime event submitted successfully")
    except Exception as e:
        print("Failed to submit to sequencer:", e)

if __name__ == "__main__":
    while True:
        for operator_url in OPERATORS:
            status = query_node_status(operator_url)
            print(f"Queried {operator_url}: {status}")

            if status["status"] == "down":
                print(f"Node {operator_url} is down. Collecting proofs...")
                proofs = collect_signatures(status["node_id"])
                downtime_event = {
                    "node": status["node_id"],
                    "event_type": "down",
                    "timestamp": status["timestamp"],
                    "proofs": proofs
                }
                print(f"Generated downtime event: {downtime_event}")
                submit_to_sequencer(downtime_event)

        time.sleep(30)  # Wait before querying again
