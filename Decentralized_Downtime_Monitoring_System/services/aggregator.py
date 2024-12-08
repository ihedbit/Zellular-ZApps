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

# Hardcoded operator details
OPERATORS = {
    "operator_1_id": {
        "socket": "http://127.0.0.1:5001",  # Example socket
        "public_key": "abcd1234..."  # Replace with the actual public key in hex
    },
    "operator_2_id": {
        "socket": "http://127.0.0.1:5002",
        "public_key": "efgh5678..."
    },
    # Add more operators as needed
}

# Hardcoded URL to ID
URLMAP = {
    "http://127.0.0.1:5001" : "operator_1",
    "http://127.0.0.1:5002" : "operator_2"
}


# Hardcoded aggregator details
AGGREGATOR = {
    "socket": "http://127.0.0.1:5002",
    "public_key": "efgh5678..."
}

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
    signers = []
    for operator_url in BASE_URLS:
        if operator_url != target_node_url:
            try:
                response = requests.post(
                    f"{operator_url}/check_node",
                    json={"node_id": URLMAP[target_node_url]}
                )
                if response.status_code == 200:
                    signatures.append(response.json())
                    signers.append(URLMAP[target_node_url])
            except Exception as e:
                print(f"Error requesting from {operator_url}: {e}")
    return signatures,signers

# Aggregate BLS signatures
def aggregate_signatures(signatures):
    sigs = [G2Element.from_bytes(base64.b64decode(sig['signature'])) for sig in signatures]
    return AugSchemeMPL.aggregate(sigs)

# Aggregate public keys
def aggregate_public_keys(signatures,signers):
    public_keys = []

    # Iterate over signers and find matching node_ids in signatures
    for signer in signers:
        for signature in signatures:
            if signer == signature["node_id"]:  # Match signer to signature's node_id
                operator = OPERATORS.get(signer)
                if operator:
                    public_key_hex = operator["public_key"]
                    public_keys.append(G1Element.from_bytes(bytes.fromhex(public_key_hex)))
    
    # Aggregate the public keys using sum, starting with a neutral G1Element()
    aggregated_key = sum(public_keys, G1Element())
    return aggregated_key

# Submit events to the sequencer
def submit_to_sequencer(event):
    try:
        zellular.send([event])  # Submit event to the sequencer
        print("Event submitted successfully to the sequencer.")
    except Exception as e:
        print(f"Error submitting event to sequencer: {e}")

# main
def main():
    for operator_url in BASE_URLS:
        if (target_status:=query_node_status(operator_url)['status']) == 'down':
            print(f"Node {target_status['node_id']} is down. Collecting proofs...")
            signatures,signers = collect_signatures(operator_url)
            if len(signatures) >= THRESHOLD:
                agg_sig = aggregate_signatures(signatures)
                agg_pub_key = aggregate_public_keys(signatures,signers)
                event = {
                    "node_id": target_status["node_id"],
                    "status": "down",
                    "timestamp": target_status["timestamp"],
                    "aggregated_signature": base64.b64encode(bytes(agg_sig)).decode('utf-8'),
                    "aggregated_public_key": bytes(agg_pub_key).hex(),
                    "signers" : signers,
                }
                submit_to_sequencer(event)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)