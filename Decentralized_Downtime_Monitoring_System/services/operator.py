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
        "public_key": "abcd1234..."  # Replace with the actual public key in hex
    },
    "operator_2_id": {
        "socket": "http://127.0.0.1:5002",
        "public_key": "efgh5678..."
    }
    # Add more operators as needed
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
            aggregated_public_key TEXT NOT NULL,
            signers TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Log the node state to SQLite
def log_state(node_id, status, timestamp, signature, aggregated_public_key, signers):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Serialize the signers list as a JSON string
    signers_json = json.dumps(signers)
    
    cursor.execute('''
        INSERT INTO logs (node_id, status, timestamp, signature, aggregated_public_key, signers)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (node_id, status, timestamp, signature, aggregated_public_key, signers_json))
    
    conn.commit()
    conn.close()

# Verify a proof from the sequencer
def verify_message(message, signature,signers,signers_aggregated_public_key):
    try:
        aggregated_public_key = [OPERATORS[operator_id]["public_key"] for operator_id in signers]
        if aggregated_public_key == signers_aggregated_public_key:
            signature_bytes = base64.b64decode(signature)
            signer_key = G2Element.from_bytes(bytes.fromhex(aggregated_public_key))
            message_bytes = message.encode('utf-8')
            return AugSchemeMPL.verify(signer_key, message_bytes, G2Element.from_bytes(signature_bytes))
        else:
            return False
        
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
    while True:
        for batch, index in zellular.batches(after=0):
            proofs = json.loads(batch)
            for proof in proofs:
                message = f"{proof['node_id']},{proof['status']},{proof['timestamp']}"
                if verify_message(message, proof['signature'],proof['signers'],proof['aggregated_public_key']):
                    log_state(proof['node_id'], 
                              proof['status'], 
                              proof['timestamp'], 
                              proof['signature'],
                              proof['aggregated_signature'],
                              proof['aggregated_public_key'],
                              proof['signers'])
                    print(f"Proof verified and logged: {proof}")
        time.sleep(5)

if __name__ == '__main__':
    init_db()
    Thread(target=read_from_sequencer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
