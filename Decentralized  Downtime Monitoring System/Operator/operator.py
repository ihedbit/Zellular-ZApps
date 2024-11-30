from flask import Flask, request, jsonify
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from zellular import Zellular, get_operators
from threading import Thread
import sqlite3
import base64
import time
import json

app = Flask(__name__)

# Database and Zellular Configuration
DATABASE = 'operator.db'
APP_NAME = "avs-downtime-monitor"
OPERATORS = get_operators()  # Fetch the list of operators
BASE_URLS = [op["socket"] for op in OPERATORS.values() if "socket" in op]
zellular = Zellular(APP_NAME, BASE_URLS[0])

# Generate operator-specific ECDSA keys (securely load in production)
PRIVATE_KEY = SigningKey.generate(curve=SECP256k1)
PUBLIC_KEY = PRIVATE_KEY.verifying_key


# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proofs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            signature TEXT NOT NULL,
            signer TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Update the SQLite database with valid proofs
def update_db(proof):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO proofs (node_id, status, timestamp, signature, signer)
        VALUES (?, ?, ?, ?, ?)
    ''', (proof['node_id'], proof['status'], proof['timestamp'], proof['signature'], proof['signer']))
    conn.commit()
    conn.close()

# Function to sign messages
def sign_message(message):
    return base64.b64encode(PRIVATE_KEY.sign(message.encode('utf-8'))).decode('utf-8')


# Function to verify proofs
def verify_message(message, signature, public_key):
    try:
        vk = VerifyingKey.from_string(base64.b64decode(public_key), curve=SECP256k1)
        vk.verify(base64.b64decode(signature), message.encode('utf-8'))
        return True
    except BadSignatureError:
        return False


# Endpoint to report the current node's status
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"node_id": "node_1", "status": "up", "timestamp": int(time.time())})


# Endpoint to check the status of another node and sign the result
@app.route('/check_node', methods=['POST'])
def check_node():
    data = request.json
    target_node_url = data['node_url']
    try:
        response = requests.get(f"{target_node_url}/status")
        status_data = response.json()
        status_message = f"{status_data['node_id']},{status_data['status']},{status_data['timestamp']}"
        signature = sign_message(status_message)
        return jsonify({
            "node_id": status_data["node_id"],
            "status": status_data["status"],
            "timestamp": status_data["timestamp"],
            "signature": signature,
            "signer": base64.b64encode(PUBLIC_KEY.to_string()).decode('utf-8')
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Function to read and validate proofs from the sequencer
def read_from_sequencer():
    while True:
        for batch, index in zellular.batches(after=0):
            proofs = json.loads(batch)
            for proof in proofs:
                message = f"{proof['node_id']},{proof['status']},{proof['timestamp']}"
                if verify_message(message, proof['signature'], proof['signer']):
                    update_db(proof)
            time.sleep(5)



if __name__ == '__main__':
    init_db()
    Thread(target=read_from_sequencer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
