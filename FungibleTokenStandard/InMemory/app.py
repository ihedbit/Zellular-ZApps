from flask import Flask, request, jsonify
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from zellular import Zellular
from threading import Thread
import base64
import requests
import time
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
#-------------------------------------
BASE_URL = "http://5.161.230.186:6001"
APP_NAME = "token_transfer"
GENESIS_ADDRESS = "your_genesis_public_key_base64"  # Replace with actual base64-encoded public key
TOKEN_NAME = "ZellularToken"
TOKEN_SYMBOL = "ZTK"
TOKEN_DECIMALS = 18
TOTAL_SUPPLY = 1000000000 * (10 ** TOKEN_DECIMALS)  # 1 billion tokens
#-------------------------------------

zellular = Zellular(APP_NAME, BASE_URL)

# Initialize balances and variables as dictionaries
balances = {}
variables = {}

# Function to initialize the system
@app.before_request
def initialize():
    # Initialize genesis address with total supply
    if GENESIS_ADDRESS not in balances:
        balances[GENESIS_ADDRESS] = TOTAL_SUPPLY
    
    # Initialize last process index
    if "last_process_indexes" not in variables:
        variables["last_process_indexes"] = 0


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

# ERC-20 like token details
@app.route('/info', methods=['GET'])
def info():
    return jsonify({
        "name": TOKEN_NAME,
        "symbol": TOKEN_SYMBOL,
        "total_supply": TOTAL_SUPPLY,
        "decimals": TOKEN_DECIMALS
    })

# Retrieve balance of an address
@app.route('/balance_of', methods=['GET'])
def balance_of():
    public_key = request.args.get('public_key')
    balance = balances.get(public_key, 0)
    return jsonify({"balance": balance})

# Token transfer endpoint
@app.route('/transfer', methods=['POST'])
def transfer():
    # Verify signature
    if not verify(request.form):
        return jsonify({"message": "Invalid signature"}), 403

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
    for batch, index in zellular.batches(after=int(variables.get("last_process_indexes", 0))):
        txs = json.loads(batch)
        for i, tx in enumerate(txs):
            if tx["operation"] == "transfer":
                _transfer(tx)  # Process each tx from the sequencer
            else:
                print("Invalid transaction", tx)
        # Update last processed index
        variables["last_process_indexes"] = index

def _transfer(tx):
    
    if not verify(tx):
        return jsonify({"message": "Invalid signature"}), 403
    
    sender_public_key = tx['public_key']
    recipient_public_key = tx['recipient']
    amount = int(tx['amount'])

    sender_balance = balances.get(sender_public_key, 0)
    recipient_balance = balances.get(recipient_public_key, 0)

    if sender_balance < amount:
        print(f"Error: insufficient funds for {sender_public_key}")
        return

    # Update balances
    balances[sender_public_key] = sender_balance - amount
    balances[recipient_public_key] = recipient_balance + amount

if __name__ == '__main__':
    Thread(target=process_txs).start()
    app.run(debug=True)