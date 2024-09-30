from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from zellular import Zellular
from threading import Thread
import base64
import requests
import time
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///token.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
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

#-------------------------------------

# Token balance model using int to represent whole tokens in smallest unit (like "wei")
class Balance(db.Model):
    public_key = db.Column(db.String(500), primary_key=True)
    amount = db.Column(db.Integer, nullable=False)


class Variable(db.Model):
    name = db.Column(db.String(500), primary_key=True)
    value = db.Column(db.String(500), nullable=False)


@app.before_first_request
def create_tables():
    db.create_all()
    # Initialize one address with 1 billion tokens
    if not Balance.query.filter_by(public_key=GENESIS_ADDRESS).first():
        genesis_balance = Balance(public_key=GENESIS_ADDRESS, amount=TOTAL_SUPPLY)
        db.session.add(genesis_balance)
        db.session.commit()
    
    if not Variable.query.filter_by(name="last_process_indexes").first():
        last_process_indexes = Variable(name="last_process_indexes", value="0")
        db.session.add(last_process_indexes)
        db.session.commit()



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
    balance = Balance.query.filter_by(public_key=public_key).first()
    if balance:
        return jsonify({"balance": balance.amount})
    else:
        return jsonify({"balance": 0})

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
    # verifier = zellular.Verifier(APP_NAME, BASE_URL)
    
    for batch, index in zellular.batches(after=int(Variable.query.filter_by(name="last_process_indexes").first())):
        txs = json.loads(batch)
        for i, tx in enumerate(txs):
            if tx["operation"] == "transfer":
                _transfer(tx)  # Process each tx from the sequencer
            else:
                print("Invalid transaction",tx)

def _transfer(tx):
    
    if not verify(tx):
        return jsonify({"message": "Invalid signature"}), 403
    
    sender_public_key = tx['public_key']
    recipient_public_key = tx['recipient']
    amount = int(tx['amount'])

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
    Thread(target=process_txs).start()
    app.run(debug=True)
