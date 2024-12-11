from flask import Flask, request, jsonify
from blspy import PrivateKey, AugSchemeMPL, G2Element
from zellular import Zellular, get_operators
import sqlite3
import base64
import time
import json
import requests
from threading import Thread

app = Flask(__name__)

# SQLite Database Configuration
DATABASE = 'operator.db'
NODE_ID = "operator_1_id"

# Generate BLS keys for the operator
SEED = b"your_unique_seed_for_this_operator"
PRIVATE_KEY = AugSchemeMPL.key_gen(SEED)
PUBLIC_KEY = PRIVATE_KEY.get_g1()

# Initialize Zellular
APP_NAME = "avs-downtime-monitor"
OPERATORS = get_operators()  # Fetch the list of operators
BASE_URLS = [op["socket"] for op in OPERATORS.values() if "socket" in op]
zellular = Zellular(APP_NAME, BASE_URLS[0])

# Hardcoded operator details
OPERATORS = {
    "operator_1_id": {
        "socket": "http://127.0.0.1:5001",  # Example socket
        "public_key": "0x1e6f881f4ac78b120e4d00adfe9b205bc12379b710cc941207c918ac65a8caa9268d4e406df4b33f19bb82820c74b938f522fa8c4b6f68763e67bbfd07ee45e4"  # Replace with the actual public key in hex
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

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            signature TEXT NOT NULL,
            non_signers TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Log the node state to SQLite
def log_state(node_id, status, timestamp, signature, aggregated_public_key, non_signers):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Serialize the signers list as a JSON string
    non_signers_json = json.dumps(non_signers)
    
    cursor.execute('''
        INSERT INTO logs (node_id, status, timestamp, signature, aggregated_public_key, non_signers)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (node_id, status, timestamp, signature, aggregated_public_key, non_signers_json))
    
    conn.commit()
    conn.close()

def aggregated_public_keys():
    # Create a list of all public keys (G2Element instances)
    public_key_list = [G2Element.from_bytes(bytes.fromhex(OPERATORS[operator_id]["public_key"][2:])) for operator_id in OPERATORS]
    
    # Sum of all public keys to form the aggregated public key
    aggregated_key = G2Element()
    for key in public_key_list:
        aggregated_key += key
    
    return aggregated_key

        
# Verify a proof from the sequencer
def verify_message(message, signature, non_signers,aggregated_key):
    try:
        # Get the public keys of the non_signers
        non_signers_public_key_list = [OPERATORS[operator_id]["public_key"] for operator_id in OPERATORS if operator_id in non_signers]
        
        # Decode the signature from base64
        signature_bytes = base64.b64decode(signature)
        
        
        # Subtract the non-signer's public key (for each non-signer)
        for public_key_hex in non_signers_public_key_list:
            non_signer_key = G2Element.from_bytes(bytes.fromhex(public_key_hex[2:]))  # Remove the '0x' prefix
            aggregated_key -= non_signer_key  # Subtract non-signer's key
        
        # Convert the message to bytes
        message_bytes = message.encode('utf-8')
        
        # Verify the signature using the adjusted aggregated public key
        return AugSchemeMPL.verify(aggregated_key, message_bytes, G2Element.from_bytes(signature_bytes))
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

# Sign a message using the operator's private key
def sign_message(message):
    message_bytes = message.encode('utf-8')
    return AugSchemeMPL.sign(PRIVATE_KEY, message_bytes)

# Endpoint to check the current node status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "node_id": NODE_ID,
        "status": "up",
        "timestamp": int(time.time()),
    })

# Endpoint to check the status of another node
@app.route('/check_node', methods=['POST'])
def check_node():
    data = request.json
    target_node_url = data['node_url']
    try:
        response = requests.get(f"{target_node_url}/status")
        target_status = response.json()
        status_message = f"{target_status['node_id']},{target_status['status']},{target_status['timestamp']}"
        signature = sign_message(status_message)
        return jsonify({
            "node_id": target_status['node_id'],
            "status": target_status['status'],
            "timestamp": target_status['timestamp'],
            "signature": base64.b64encode(bytes(signature)).decode('utf-8'),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Read and validate proofs from the sequencer
def read_from_sequencer():
    aggregated_key = aggregated_public_keys()
    while True:
        for batch, index in zellular.batches(after=0):
            proofs = json.loads(batch)
            for proof in proofs:
                message = f"{proof['node_id']},{proof['status']},{proof['timestamp']}"
                if verify_message(message, proof['signature'],proof['non_signers'],aggregated_key):
                    log_state(proof['node_id'], 
                              proof['status'], 
                              proof['timestamp'], 
                              proof['signature'],
                              proof['aggregated_signature'],
                              proof['non_signers'])
                    print(f"Proof verified and logged: {proof}")
        time.sleep(5)

if __name__ == '__main__':
    init_db()
    Thread(target=read_from_sequencer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
