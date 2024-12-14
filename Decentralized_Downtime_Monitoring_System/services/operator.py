import sys
from flask import Flask, request, jsonify
from blspy import PrivateKey, AugSchemeMPL, G2Element,G1Element
from zellular import Zellular, get_operators
import sqlite3
import base64
import time
import json
import requests
from threading import Thread

app = Flask(__name__)

# Hardcoded operator details
OPERATORS = {
    "operator_1_id": {
        "socket": "http://127.0.0.1:5001",
        "public_key": "a08e52124e2192788164bd06e71287499ce167cc0a7b98bb9a7c27519662eb478bcdf4e53f7468557b617152cf359bea"
    },
    "operator_2_id": {
        "socket": "http://127.0.0.1:5002",
        "public_key": "a9b5d8b9dffc550cabc7729e999c188160e3f019787b2f1f93f770267ac851422c4651a0274d92f93067f952a9b7b012"
    },
    "operator_3_id": {
        "socket": "http://127.0.0.1:5003",
        "public_key": "8255bbca4f620830cbb6c1f30f13b65506d516aeb724433ba0931ed3379dbc9e6ad880a75a66f5aa40a73d507755b879"
    },
    "operator_4_id": {
        "socket": "http://127.0.0.1:5004",
        "public_key": "87f745ee77dd2fe55da523eec6ab38d497589eb307e1e253cec89aa22bebb066d86066192270a140bcc5ae38e79f8cd4"
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

# SQLite Database Configuration
DATABASE = 'operator.db'
NODE_ID = sys.argv[1]  # Node ID passed as a command-line argument
PORT = int(sys.argv[2])  # Port number passed as a command-line argument

# Generate BLS keys for the operator
SEED = b"seed_related_to_zellular_operator_4_id"
PRIVATE_KEY = AugSchemeMPL.key_gen(SEED)
PUBLIC_KEY = PRIVATE_KEY.get_g1()

# Initialize Zellular
APP_NAME = "avs-downtime-monitor"
ZELLULAR_OPERATORS = get_operators()
BASE_URLS = [op["socket"] for op in ZELLULAR_OPERATORS.values() if "socket" in op]

zellular = Zellular(APP_NAME, BASE_URLS[0])

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
    public_key_list = []
    for operator_id, details in OPERATORS.items():
        try:
            
            public_key_bytes = bytes.fromhex(details["public_key"])  # No prefix assumed
            if len(public_key_bytes) != G1Element.SIZE:
                raise ValueError(f"Invalid public key length for {operator_id}: {len(public_key_bytes)} bytes")
            public_key_list.append(G1Element.from_bytes(public_key_bytes))
        except Exception as e:
            print(f"Error processing public key for {operator_id}: {e}")
    
    # Aggregate all valid public keys
    aggregated_key = sum(public_key_list, G1Element())
    return aggregated_key


        
# Verify a proof from the sequencer
def verify_message(message, signature, non_signers, aggregated_key):
    try:
        # Get the public keys of the non-signers
        non_signers_public_key_list = [OPERATORS[operator_id]["public_key"] for operator_id in non_signers]
        
        # Adjust the aggregated key by removing non-signers' keys
        for public_key_hex in non_signers_public_key_list:
            non_signer_key = G1Element.from_bytes(bytes.fromhex(public_key_hex))  # Adjust to G1Element
            aggregated_key -= non_signer_key
        
        # Verify the signature
        message_bytes = message.encode('utf-8')
        
        # `signature` should be a G2Element, so ensure it's deserialized if passed as a string
        if isinstance(signature, str):
            signature = G2Element.from_bytes(base64.b64decode(signature))
        
        # Perform verification
        return AugSchemeMPL.verify(aggregated_key, message_bytes, signature)
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
    app.run(host='0.0.0.0', port=PORT)
