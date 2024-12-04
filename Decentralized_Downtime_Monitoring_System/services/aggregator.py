from blspy import G1Element, G2Element, AugSchemeMPL
from zellular import Zellular, get_operators
import requests
import time
import base64
import json

# Configuration
OPERATORS = get_operators()  # Fetch the list of operators dynamically
BASE_URLS = [op["socket"] for op in OPERATORS.values() if "socket" in op]
APP_NAME = "avs-downtime-monitor"
zellular = Zellular(APP_NAME, BASE_URLS[0])
THRESHOLD = 2  # Minimum number of valid signatures required

# Query a node's status
def query_node_status(node_url):
    try:
        response = requests.get(f"{node_url}/status")
        return response.json()
    except Exception as e:
        return {"node_id": node_url, "status": "down", "timestamp": int(time.time())}

# Collect signatures from other operators
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
                print(f"Error requesting from {operator_url}: {e}")
    return signatures

# Aggregate BLS signatures
def aggregate_signatures(signatures):
    sigs = [G2Element.from_bytes(base64.b64decode(sig['signature'])) for sig in signatures]
    return AugSchemeMPL.aggregate(sigs)

# Aggregate public keys
def aggregate_public_keys(signatures):
    public_keys = [G1Element.from_bytes(bytes.fromhex(sig['public_key'])) for sig in signatures]
    return sum(public_keys, G1Element())

# Submit events to the sequencer
def submit_to_sequencer(event):
    try:
        zellular.send([event])  # Submit event to the sequencer
        print("Event submitted successfully to the sequencer.")
    except Exception as e:
        print(f"Error submitting event to sequencer: {e}")

if __name__ == "__main__":
    while True:
        for operator_url in BASE_URLS:
            target_status = query_node_status(operator_url)
            if target_status['status'] == 'down':
                print(f"Node {target_status['node_id']} is down. Collecting proofs...")
                signatures = collect_signatures(operator_url)
                if len(signatures) >= THRESHOLD:
                    agg_sig = aggregate_signatures(signatures)
                    agg_pub_key = aggregate_public_keys(signatures)
                    event = {
                        "node_id": target_status["node_id"],
                        "status": "down",
                        "timestamp": target_status["timestamp"],
                        "aggregated_signature": base64.b64encode(bytes(agg_sig)).decode('utf-8'),
                        "aggregated_public_key": bytes(agg_pub_key).hex(),
                        "proofs": signatures
                    }
                    submit_to_sequencer(event)
        time.sleep(30)
