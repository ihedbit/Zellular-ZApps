from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
import base64
import requests
import zellular
from threading import Thread
import time
import json
import logging
from uuid import uuid4

# Initialize the Flask app and SQLAlchemy for DB interaction
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///squared.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Zellular configuration
base_url = "http://5.161.230.186:6001"
app_name = "squared_task"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database model to store the number and its square
class Square(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_to_be_squared = db.Column(db.Integer, nullable=False)
    number_squared = db.Column(db.Integer, nullable=False)

@app.before_first_request
def create_tables():
    db.create_all()

# Function to verify the transaction signature
def verify_transaction(transaction):
    try:
        public_key = base64.b64decode(transaction['public_key'])
        signature = base64.b64decode(transaction['signature'])
        message = ','.join([str(transaction[key]) for key in ['task_id', 'number_to_be_squared']]).encode('utf-8')
        vk = VerifyingKey.from_string(public_key, curve=SECP256k1)
        vk.verify(signature, message)
        return True
    except (BadSignatureError, ValueError) as e:
        logger.error(f"Signature verification failed: {e}")
        return False

# Function to post tasks to Zellular (creating squaring tasks)
@app.route('/post_task', methods=['POST'])
def post_task():
    # Verify signature
    if not verify_transaction(request.form):
        return jsonify({"message": "Invalid signature"}), 403

    sender_public_key = request.form['public_key']
    task_id = request.form["task_id"]
    number_to_be_squared = int(request.form["number_to_be_squared"])
    number_squared = number_to_be_squared ** 2

    # Prepare the transaction for Zellular
    tx = {
        "operation": "square_number",
        "tx_id": str(uuid4()),  # Unique transaction ID
        "public_key": sender_public_key,
        "task_id": task_id,
        "number_to_be_squared": number_to_be_squared,
        "number_squared": number_squared,
        "timestamp": int(time.time())
    }

    # Post the transaction to Zellular
    zresponse = requests.put(f"{base_url}/node/{app_name}/batches", json=[tx])

    if zresponse.status_code != 200:
        return jsonify({"message": f"Error submitting task to Zellular: {zresponse.status_code}"}), 500

    logger.info(f"Task {task_id} posted: {number_to_be_squared} squared is {number_squared}")
    return jsonify({"message": "Task successfully posted", "task_id": task_id})

# Process finalized transactions from Zellular and store the results in the database
def process_loop():
    verifier = zellular.Verifier(app_name, base_url)
    last_index = 0

    while True:
        # Fetch finalized batches from Zellular
        for batch, index in verifier.batches(after=last_index):
            txs = json.loads(batch)
            for tx in txs:
                if tx.get("operation") == "square_number":
                    process_task(tx)
            last_index = index
        time.sleep(1)  # Avoid tight loop

# Function to process each task and save the results in the database
def process_task(transaction):
    if not verify_transaction(transaction):
        logger.error(f"Invalid transaction: {transaction}")
        return

    task_id = transaction["task_id"]
    number_to_be_squared = int(transaction["number_to_be_squared"])
    number_squared = int(transaction["number_squared"])

    # Check if the task is already processed
    existing_task = Square.query.filter_by(number_to_be_squared=number_to_be_squared).first()
    if existing_task:
        logger.info(f"Task {task_id} is already processed.")
        return

    # Save the squared result to the database
    new_task = Square(number_to_be_squared=number_to_be_squared, number_squared=number_squared)
    db.session.add(new_task)
    db.session.commit()
    logger.info(f"Task {task_id}: Saved {number_to_be_squared} squared as {number_squared}.")

if __name__ == '__main__':
    # Start the background process to listen for finalized transactions from Zellular
    Thread(target=process_loop).start()
    # Start the Flask app
    app.run(debug=True)
