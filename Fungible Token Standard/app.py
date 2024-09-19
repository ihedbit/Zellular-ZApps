from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import base64
import requests
from threading import Thread
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///token_transfers.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
zsequencer_url = 'http://localhost:8323/node/transactions'

# Token balance model
class Balance(db.Model):
    public_key = db.Column(db.String(500), primary_key=True)
    amount = db.Column(db.Float, nullable=False, default=10)  # Default to 10 tokens for each user

@app.before_first_request
def create_tables():
    db.create_all()

# Function to verify signatures
def verify_transaction(transaction):
    message = ','.join([transaction[key] for key in ['recipient', 'amount']]).encode('utf-8')
    try:
        public_key = base64.b64decode(transaction['public_key'])
        signature = base64.b64decode(transaction['signature'])
        vk = VerifyingKey.from_string(public_key, curve=SECP256k1)
        vk.verify(signature, message)
    except (BadSignatureError, ValueError):
        return False
    return True

# Token transfer endpoint
@app.route('/transfer', methods=['POST'])
def transfer_tokens():
    # Verify signature
    if not verify_transaction(request.form):
        return jsonify({"message": "Invalid signature"}), 403
    
    sender_public_key = request.form['public_key']
    recipient_public_key = request.form['recipient']
    amount = float(request.form['amount'])
    
    sender_balance = Balance.query.filter_by(public_key=sender_public_key).first()
    recipient_balance = Balance.query.filter_by(public_key=recipient_public_key).first()

    if not sender_balance or sender_balance.amount < amount:
        return jsonify({"message": "Insufficient balance"}), 403

    # Add the transaction to Zellular sequencer
    data = {
        'transactions': [{'public_key': sender_public_key, 'recipient': recipient_public_key, 'amount': amount}],
        'timestamp': int(time.time())
    }
    headers = {"Content-Type": "application/json"}
    requests.put(zsequencer_url, json=data, headers=headers)

    return {'success': True}

# Process finalized transactions from the Zellular sequencer
def process_loop():
    last = 0
    while True:
        params = {"after": last, "states": ["finalized"]}
        response = requests.get(zsequencer_url, params=params)
        finalized_txs = response.json().get("data")
        if not finalized_txs:
            time.sleep(1)
            continue

        last = max(tx["index"] for tx in finalized_txs)
        sorted_numbers = sorted([t["index"] for t in finalized_txs])
        print(f"\nReceived finalized indexes: [{sorted_numbers[0]}, ..., {sorted_numbers[-1]}]")

        for tx in finalized_txs:
            process_transfer(tx)

def process_transfer(transaction):
    sender_public_key = transaction['public_key']
    recipient_public_key = transaction['recipient']
    amount = float(transaction['amount'])

    sender_balance = Balance.query.filter_by(public_key=sender_public_key).first()
    recipient_balance = Balance.query.filter_by(public_key=recipient_public_key).first()

    if not sender_balance or sender_balance.amount < amount:
        print(f"Error: insufficient funds for {sender_public_key}")
        return

    # Update balances
    sender_balance.amount -= amount
    if recipient_balance:
        recipient_balance.amount += amount
    else:
        new_recipient_balance = Balance(public_key=recipient_public_key, amount=amount)
        db.session.add(new_recipient_balance)

    db.session.commit()

if __name__ == '__main__':
    Thread(target=process_loop).start()
    app.run(debug=True)
