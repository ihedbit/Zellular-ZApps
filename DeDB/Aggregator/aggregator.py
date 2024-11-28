import requests
import time
import base64
import json
from pyfrost import FrostAggregator

OPERATORS = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002"
]
SEQUENCER_URL = "http://zellular-sequencer.example.com"
THRESHOLD = 2  # Adjust to the desired threshold

# Load the public key
with open('aggregator_public_key.json', 'r') as f:
    public_key_data = json.load(f)
public_key = FrostAggregator.from_dict(public_key_data)


# Query a node's status
def query_node_status(node_url):
    try:
        response = requests.get(f"{node_url}/status")
        return response.json()
    except Exception as e:
        return {"node_id": node_url, "status": "down", "timestamp": int(time.time())}


# Collect partial signatures from operators
def collect_signatures(target_node_url):
    signatures = []
    for operator_url in OPERATORS:
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


# Combine partial signatures to generate a threshold signature
def combine_signatures(message, partial_signatures):
    valid_signatures = [
        (sig['signer_id'], base64.b64decode(sig['signature']))
        for sig in partial_signatures
    ]
    if len(valid_signatures) >= THRESHOLD:
        return public_key.combine(message.encode('utf-8'), valid_signatures)
    return None


# Submit events to the sequencer
def submit_to_sequencer(event):
    try:
        response = requests.post(SEQUENCER_URL, json=event)
        if response.status_code == 200:
            print("Event submitted successfully to the sequencer.")
        else:
            print(f"Failed to submit event: {response.text}")
    except Exception as e:
        print(f"Error submitting event to sequencer: {e}")


if __name__ == "__main__":
    while True:
        for operator_url in OPERATORS:
            # Query the target node's status
            target_status = query_node_status(operator_url)
            print(f"Queried {operator_url}: {target_status}")

            if target_status["status"] == "down":
                print(f"Node {operator_url} is down. Collecting signatures...")

                # Collect partial signatures
                collected_signatures = collect_signatures(operator_url)

                # Combine partial signatures
                message = f"{target_status['node_id']},{target_status['status']},{target_status['timestamp']}"
                threshold_signature = combine_signatures(message, collected_signatures)

                if threshold_signature:
                    downtime_event = {
                        "node_id": target_status["node_id"],
                        "event_type": "down",
                        "timestamp": target_status["timestamp"],
                        "threshold_signature": base64.b64encode(threshold_signature).decode('utf-8'),
                        "proofs": collected_signatures
                    }
                    print(f"Generated downtime event: {downtime_event}")

                    # Submit the downtime event to the sequencer
                    submit_to_sequencer(downtime_event)

        time.sleep(30)  # Wait before querying again
