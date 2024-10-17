from flask import Flask, request, jsonify
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from zellular import Zellular, get_operators
from threading import Thread
from uuid import uuid4
import base64
import requests
import time
import json
import random
import hashlib
import os
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

#-------------------------------------
# Fetch the list of operators and extract their socket URLs
def get_operator_urls():
    operators = get_operators()
    sockets = [op["socket"] for op in operators.values() if "socket" in op]
    return sockets

#-------------------------------------
# Initialize the BASE_URLS dynamically from the fetched operators
BASE_URLS = get_operator_urls()
APP_NAME = "APP_NAME"
GENESIS_ADDRESS = "your_genesis_public_key_base64"  # Replace with actual base64-encoded public key
TOKEN_NAME = "ZellularToken"
TOKEN_SYMBOL = "ZTK"
TOKEN_DECIMALS = 18
TOTAL_SUPPLY = 1000000000 * (10 ** TOKEN_DECIMALS)  # 1 billion tokens

DB_FILE = 'zelldb.sqlite'

# Initialize Zellular
zellular = Zellular(APP_NAME, BASE_URLS[0])

#-------------------------------------
# Initialize SQLite DB and tables
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create tables for balances and variables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            public_key TEXT PRIMARY KEY,
            balance INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS variables (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Function to initialize the system
@app.before_first_request
def initialize():
    init_db()

    # Load or initialize balances and variables
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if genesis address exists, if not, initialize it with total supply
    cursor.execute('SELECT balance FROM balances WHERE public_key=?', (GENESIS_ADDRESS,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO balances (public_key, balance) VALUES (?, ?)', (GENESIS_ADDRESS, TOTAL_SUPPLY))
        print("Initialized genesis address with total supply.")

    # Check if 'last_process_indexes' exists in variables, if not, initialize it
    cursor.execute('SELECT value FROM variables WHERE key=?', ('last_process_indexes',))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO variables (key, value) VALUES (?, ?)', ('last_process_indexes', '0'))
        print("Initialized variables with default values.")

    conn.commit()
    conn.close()


# Function to verify signatures
def verify(tx):
    message = ','.join([tx[key] for key in ['recipient', 'amount']]).encode('utf-8')
    try:
        public_key = base64.b64decode(tx['public_key'])
        signature = base64.b64decode(tx['signature'])
        vk = VerifyingKey.from_string(public_key, curve=SECP256k1)
        vk.verify(signature, message)
    except (BadSignatureError, ValueError):
        return False
    return True


# Retrieve balance of an address
@app.route('/balance_of', methods=['GET'])
def balance_of():
    public_key = request.args.get('public_key')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM balances WHERE public_key=?', (public_key,))
    result = cursor.fetchone()
    balance = result[0] if result else 0
    conn.close()

    return jsonify({"balance": balance})


# Token transfer endpoint
@app.route('/transfer', methods=['POST'])
def transfer():
    # Verify signature
    if not verify(request.form):
        return jsonify({"message": "Invalid signature"}), 403

    # Randomly select a base URL from the list for this transaction
    selected_base_url = random.choice(BASE_URLS)
    zellular.base_url = selected_base_url  # Update the Zellular instance with the selected URL

    # Add the tx to Zellular sequencer
    tx = {
        "operation": "transfer",
        "tx_id": str(uuid4()),  # Unique tx ID
        "public_key": request.form['public_key'],
        "recipient": request.form['recipient'],
        "amount": int(request.form['amount']),
    }
    txs = [tx]
    zellular.send(txs)

    return {'success': True}


# Process finalized txs from the Zellular sequencer
def process_txs():
    while True:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get last processed index from the database
        cursor.execute('SELECT value FROM variables WHERE key=?', ('last_process_indexes',))
        last_index = int(cursor.fetchone()[0])

        for batch, index in zellular.batches(after=last_index):
            txs = json.loads(batch)
            for i, tx in enumerate(txs):
                if tx["operation"] == "transfer":
                    _transfer(tx)  # Process each tx from the sequencer
                else:
                    print("Invalid transaction", tx)
            # Update last processed index
            cursor.execute('UPDATE variables SET value=? WHERE key=?', (index, 'last_process_indexes'))

        conn.commit()
        conn.close()
        time.sleep(1)  # Adjust the interval if necessary


def _transfer(tx):
    if not verify(tx):
        print("Invalid signature for transaction")
        return

    sender_public_key = tx['public_key']
    recipient_public_key = tx['recipient']
    amount = int(tx['amount'])

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get balances of sender and recipient
    cursor.execute('SELECT balance FROM balances WHERE public_key=?', (sender_public_key,))
    sender_balance = cursor.fetchone()[0] if cursor.fetchone() else 0
    cursor.execute('SELECT balance FROM balances WHERE public_key=?', (recipient_public_key,))
    recipient_balance = cursor.fetchone()[0] if cursor.fetchone() else 0

    if sender_balance < amount:
        print(f"Error: insufficient funds for {sender_public_key}")
        conn.close()
        return

    # Update balances
    cursor.execute('UPDATE balances SET balance=? WHERE public_key=?', (sender_balance - amount, sender_public_key))
    cursor.execute('UPDATE balances SET balance=? WHERE public_key=?', (recipient_balance + amount, recipient_public_key))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    # Start the transaction processing thread
    Thread(target=process_txs, daemon=True).start()
    # Run the Flask app
    app.run(debug=True)
