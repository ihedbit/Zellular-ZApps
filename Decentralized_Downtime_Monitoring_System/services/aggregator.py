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
        "public_key": "0x1e6f881f4ac78b120e4d00adfe9b205bc12379b710cc941207c918ac65a8caa9268d4e406df4b33f19bb82820c74b938f522fa8c4b6f68763e67bbfd07ee45e4"  
    },
    "operator_2_id": {
        "socket": "http://127.0.0.1:5002",
        "public_key": "0x7ac3957dfb95f0c876062c442f6f81cc8d51d573b848e77f8a75f1f0ab8b5199d6b8b03d29a0acb61cde264c69c79872fd383d8f24c28dff5d865285d144e100fd"
    },
    "operator_3_id": {
        "socket": "http://127.0.0.1:5003",
        "public_key": "0x89cd32f469874b4248c5de2400e33f3c3b2b51e358387fe5b85e1f98a309350559003ee70c8405d0df0f7da61172ec6f6d79ff4586ef3d9f728cf57823cc515c"
    },
    "operator_4_id": {
        "socket": "http://127.0.0.1:5004",
        "public_key": "0x9e3b0410577a77c0880c367d8a163a3c19e63e12b4e438e88b3981be88c3db23f17e4da9025ffcd74632a263f26e7983a9ec6de115e9dce825b20713aaf7bc7a6"
    },
    # Add more operators as needed
}

# Hardcoded URL to ID
URLMAP = {
    "http://127.0.0.1:5001" : "operator_1_id",
    "http://127.0.0.1:5002" : "operator_2_id",
    "http://127.0.0.1:5003" : "operator_3_id",
    "http://127.0.0.1:5004" : "operator_4_id"
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
    non_signers = []
    for operator_url in BASE_URLS:
        if operator_url != target_node_url:
            try:
                response = requests.post(
                    f"{operator_url}/check_node",
                    json={"node_id": URLMAP[target_node_url]}
                )
                if response.status_code == 200:
                    signatures.append(response.json())
                    
            except Exception as e:
                non_signers.append(URLMAP[target_node_url])
                print(f"Error requesting from {operator_url}: {e}")
    return signatures,non_signers

# Aggregate BLS signatures
def aggregate_signatures(signatures):
    sigs = [G2Element.from_bytes(base64.b64decode(sig['signature'])) for sig in signatures]
    return AugSchemeMPL.aggregate(sigs)


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
            signatures,non_signers = collect_signatures(operator_url)
            if len(signatures) >= THRESHOLD:
                agg_sig = aggregate_signatures(signatures)
                event = {
                    "node_id": target_status["node_id"],
                    "status": "down",
                    "timestamp": target_status["timestamp"],
                    "aggregated_signature": base64.b64encode(bytes(agg_sig)).decode('utf-8'),
                    "non_signers" : non_signers,
                }
                submit_to_sequencer(event)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)