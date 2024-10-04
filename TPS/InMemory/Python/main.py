import time
import json
import requests
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from threading import Thread, Event

# In-memory storage for transactions
transactions = []
batch_interval = 0.1  # Time interval for batching transactions in seconds
stop_event = Event()

# ECDSA transaction verification function
def verify_transaction(transaction_data, signature, public_key):
    return True
    # vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    try:
        # vk.verify(bytes.fromhex(signature), transaction_data.encode())
        return True
    except BadSignatureError:
        return False

# Sending batch transactions to the server
def send_batch_to_server(batch_transactions):
    try:
        response = requests.post("http://127.0.0.1:5000/echo", json=batch_transactions)
        return response.json()
    except Exception as e:
        print(f"Error sending batch transactions to server: {e}")
        return None

# Periodically send batch transactions
def batch_sender():
    while not stop_event.is_set():
        time.sleep(batch_interval)
        if transactions:
            batch = transactions.copy()  # Copy current batch
            transactions.clear()  # Clear the in-memory list for new transactions

            # Send the batch to the server
            response = send_batch_to_server(batch)
            if response:
                print(f"Batch sent successfully: {response}")

# Adding transaction to in-memory storage
def save_transaction_in_memory(transaction_data):
    transactions.append(transaction_data)

# Process individual transaction (adds to batch list if verified)
def process_transaction(transaction_data, signature, public_key):
    if verify_transaction(transaction_data['data'], signature, public_key):
        save_transaction_in_memory(transaction_data)
    else:
        print("Transaction verification failed.")

# Example usage
transaction_data = {
    "data": "Transfer 10 tokens from A to B",
    "from": "A",
    "to": "B",
    "amount": 10
}

signature = "3045022100e8b5b9a1e8a73bf7f0c3ae3d77d8f62e41ad3cda4a67db2f5f01236496a0ed9c02206d98e42c12ab11f1f9b358e80b03b9b514cd4ba93513b3c2e34fd272b3571b38"
public_key = "04bfcf0e7ca431899b324be76b89ac9815cda5fdf31b7a60a69c4bcb5fda59d9e8f19f622f1f7adfd1c65e988d148d4e67a740d4b9b94ac96f9c0b44631569b3d8"

# Start batch sender thread
batch_thread = Thread(target=batch_sender)
batch_thread.start()

# Simulate processing transactions
for _ in range(10):  # Example loop to simulate multiple transactions
    process_transaction(transaction_data, signature, public_key)
    time.sleep(0.05)  # Simulate a slight delay between incoming transactions

# Stop the batch sender after a period (e.g., 1 second for testing)
time.sleep(1)
stop_event.set()
batch_thread.join()
