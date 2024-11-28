from flask import Flask, request, jsonify
from pyfrost import FrostSigner
from threading import Thread
import sqlite3
import base64
import time
import json
import requests

app = Flask(__name__)
DATABASE = 'operator.db'
SEQUENCER_BASE_URL = "http://zellular-sequencer.example.com"  # Replace with the actual URL

# Load the operator's key share (securely load this in production)
with open('key_share.json', 'r') as f:
    key_share_data = json.load(f)
key_share = FrostSigner.from_dict(key_share_data)


# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            signature TEXT NOT NULL,
            signer_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Function to sign a message
def sign_message(message):
    partial_signature = key_share.sign(message.encode('utf-8'))
    return base64.b64encode(partial_signature).decode('utf-8')


# Endpoint to report the current node's status
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"node_id": "node_1", "status": "up", "timestamp": int(time.time())})


# Endpoint to check another node's status and sign the result
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
            "signer_id": key_share.identifier
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Function to continuously read proofs from the sequencer and update the database
def read_from_sequencer():
    while True:
        try:
            response = requests.get(f"{SEQUENCER_BASE_URL}/batch")
            if response.status_code == 200:
                proofs = response.json()
                for proof in proofs:
                    update_db(proof)
        except Exception as e:
            print(f"Error reading from sequencer: {e}")
        time.sleep(5)


# Update the SQLite database with a proof
def update_db(proof):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO node_states (node_id, status, timestamp, signature, signer_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (proof['node_id'], proof['status'], proof['timestamp'], proof['signature'], proof['signer_id']))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    Thread(target=read_from_sequencer, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
