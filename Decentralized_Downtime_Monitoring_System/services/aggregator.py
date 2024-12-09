from blspy import G1Element, G2Element, AugSchemeMPL
import requests
import time
import base64
import json

# Configuration
OPERATORS = {
    "operator_1_id": {
        "socket": "http://127.0.0.1:5001",
        "public_key": "abcd1234..."  # Replace with actual public key (hex)
    },
    "operator_2_id": {
        "socket": "http://127.0.0.1:5002",
        "public_key": "efgh5678..."  # Replace with actual public key (hex)
    },
}
URLMAP = {op["socket"]: operator_id for operator_id, op in OPERATORS.items()}
BASE_URLS = list(URLMAP.keys())
THRESHOLD = 2  # Minimum valid signatures required

# Query a node's status
def query_node_status(node_url):
    try:
        response = requests.get(f"{node_url}/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {"node_id": URLMAP[node_url], "status": "down", "timestamp": int(time.time())}

# Collect signatures from other operators
def collect_signatures(target_node_url):
    signatures = []
    signers = []
    for operator_url in BASE_URLS:
        if operator_url != target_node_url:
            try:
                response = requests.post(
                    f"{operator_url}/check_node",
                    json={"node_url": target_node_url},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    signatures.append(data)
                    signers.append(data["node_id"])
            except requests.RequestException as e:
                print(f"Error requesting from {operator_url}: {e}")
    return signatures, signers

# Aggregate BLS signatures
def aggregate_signatures(signatures):
    sigs = [G2Element.from_bytes(base64.b64decode(sig["signature"])) for sig in signatures]
    return AugSchemeMPL.aggregate(sigs)

# Aggregate public keys
def aggregate_public_keys(signers):
    public_keys = []
    for signer in signers:
        operator = OPERATORS.get(signer)
        if operator:
            public_key_hex = operator["public_key"]
            public_keys.append(G1Element.from_bytes(bytes.fromhex(public_key_hex)))
    return sum(public_keys, G1Element())

# Main function
def main():
    for operator_url in BASE_URLS:
        target_status = query_node_status(operator_url)
        if target_status["status"] == "down":
            print(f"Node {target_status['node_id']} is down. Collecting proofs...")
            signatures, signers = collect_signatures(operator_url)
            if len(signatures) >= THRESHOLD:
                agg_sig = aggregate_signatures(signatures)
                agg_pub_key = aggregate_public_keys(signers)
                event = {
                    "node_id": target_status["node_id"],
                    "status": "down",
                    "timestamp": target_status["timestamp"],
                    "aggregated_signature": base64.b64encode(bytes(agg_sig)).decode("utf-8"),
                    "aggregated_public_key": bytes(agg_pub_key).hex(),
                    "signers": signers,
                }
                print("Aggregated event:", event)
            else:
                print(f"Insufficient signatures for node {target_status['node_id']}.")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)
