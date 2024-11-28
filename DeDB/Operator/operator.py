from flask import Flask, request, jsonify
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from threading import Thread
from zellular import Zellular
import sqlite3
import base64
import time
import json
import requests

app = Flask(__name__)
DATABASE = 'operator.db'
APP_NAME = "avs-downtime-monitor"
SEQUENCER_BASE_URL = "http://zellular-sequencer.example.com"  # Replace with the actual URL
zellular = Zellular(APP_NAME, SEQUENCER_BASE_URL)

# Generate ECDSA private key (in production, securely load it from a file or environment)
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


# Function to sign messages using ECDSA
def sign_message(message):
    signature = PRIVATE_KEY.sign(message.encode('utf-8'))
    return base64.b64encode(signature).decode('utf-8')


# Function to verify a message and its signature using a public key
def verify_message(message, signature, public_key):
    try:
        vk = VerifyingKey.from_string(base64.b64decode(public_key), curve=SECP256k1)
        vk.verify(base64.b64decode(signature), message.encode('utf-8'))
        return True
    except BadSignatureError:
        return False
    except Exception as e:
        print(f"Verification error: {e}")
        return False


# Endpoint to check the status of another node and return a signed result
@app.route('/check_node', methods=['POST'])
def check_node():
    data = request.json
    target_node_url = data['node_url']
    try:
        # Query the status of the target node
        response = requests.get(f"{target_node_url}/status")
        status_data = response.json()
        status_message = f"{status_data['node_id']},{status_data['status']},{status_data['timestamp']}"
        
        # Sign the status message
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


# Endpoint to report the current node's status
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"node_id": "node_1", "status": "up", "timestamp": int(time.time())})


# Function to continuously read proofs from the sequencer and update the database
def read_from_sequencer():
    while True:
        for batch, index in zellular.batches(after=0):  # Adjust the starting index as needed
            events = json.loads(batch)
            for proof in events:
                # Verify the proof
                status_message = f"{proof['node_id']},{proof['status']},{proof['timestamp']}"
                if verify_message(status_message, proof['signature'], proof['signer']):
                    update_db(proof)
                    print(f"Verified and updated: {proof}")
                else:
                    print(f"Invalid proof: {proof}")
            time.sleep(1)


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


if __name__ == '__main__':
    init_db()
    Thread(target=read_from_sequencer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
