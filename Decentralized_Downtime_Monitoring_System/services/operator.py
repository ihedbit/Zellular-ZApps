from flask import Flask, request, jsonify
from blspy import PrivateKey, AugSchemeMPL, G2Element
import sqlite3
import base64
import time
import json
from threading import Thread

app = Flask(__name__)

# SQLite Configuration
DATABASE = "operator.db"
NODE_ID = "operator_1"  # Unique node ID

# Generate BLS Keys
SEED = b"your_unique_seed_for_this_operator"
PRIVATE_KEY = AugSchemeMPL.key_gen(SEED)
PUBLIC_KEY = PRIVATE_KEY.get_g1()

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            signature TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Log state to the database
def log_state(node_id, status, timestamp, signature):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (node_id, status, timestamp, signature)
        VALUES (?, ?, ?, ?)
    ''', (node_id, status, timestamp, signature))
    conn.commit()
    conn.close()

# Sign a message
def sign_message(message):
    message_bytes = message.encode("utf-8")
    signature = AugSchemeMPL.sign(PRIVATE_KEY, message_bytes)
    return signature

# Node status endpoint
@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "node_id": NODE_ID,
        "status": "up",
        "timestamp": int(time.time()),
    })

# Check another node's status
@app.route("/check_node", methods=["POST"])
def check_node():
    data = request.json
    target_node_url = data.get("node_url")
    try:
        response = requests.get(f"{target_node_url}/status", timeout=5)
        target_status = response.json()
        message = f"{target_status['node_id']},{target_status['status']},{target_status['timestamp']}"
        signature = sign_message(message)
        return jsonify({
            "node_id": target_status["node_id"],
            "status": target_status["status"],
            "timestamp": target_status["timestamp"],
            "signature": base64.b64encode(bytes(signature)).decode("utf-8"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)
