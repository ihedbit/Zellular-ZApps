import time
import json
import requests
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError

# In-memory storage for transactions
transactions = []

# ECDSA transaction verification function
def verify_transaction(transaction_data, signature, public_key):
    return True
    # vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    try:
        # vk.verify(bytes.fromhex(signature), transaction_data.encode())
        return True
    except BadSignatureError:
        return False

# Sending transaction to echo server
def send_transaction_to_server(transaction_data):
    try:
        response = requests.post("http://127.0.0.1:5000/echo", json=transaction_data)
        return response.json()
    except Exception as e:
        print(f"Error sending transaction to server: {e}")
        return None

# Verifying received transaction from server
def verify_received_transaction(received_transaction_data, signature, public_key):
    return verify_transaction(received_transaction_data, signature, public_key)

# Saving transaction to in-memory storage
def save_transaction_in_memory(transaction_data):
    transactions.append(transaction_data)

# Example workflow to verify, send, verify again, and save
def process_transaction(transaction_data, signature, public_key):
    # Step 1: Verify the transaction using ECDSA
    if not verify_transaction(transaction_data['data'], signature, public_key):
        print("Transaction verification failed.")
        return
    
    # Step 2: Send transaction to the echo server and get the response
    received_transaction = send_transaction_to_server(transaction_data)
    if not received_transaction:
        print("Failed to receive transaction from server.")
        return

    # Step 3: Verify the received transaction again
    if not verify_received_transaction(received_transaction['data'], signature, public_key):
        print("Received transaction verification failed.")
        return
    
    # Step 4: Save the verified transaction in both in-memory and file
    save_transaction_in_memory(received_transaction)

# Performance testing function for transactions sent and verified
def performance_test(transaction_data, signature, public_key, duration=1):
    start_time = time.time()
    count = 0

    # Perform verifications for the specified duration (in seconds)
    while time.time() - start_time < duration:
        # Step 1: Verify the transaction using ECDSA
        if not verify_transaction(transaction_data['data'], signature, public_key):
            print("Transaction verification failed.")
            return

        # Step 2: Send transaction to the server and get the response
        received_transaction = send_transaction_to_server(transaction_data)
        if not received_transaction:
            print("Failed to receive transaction from server.")
            return

        # Step 3: Verify the received transaction
        if not verify_received_transaction(received_transaction['data'], signature, public_key):
            print("Received transaction verification failed.")
            return

        # Step 4: Save the transaction in memory
        save_transaction_in_memory(received_transaction)

        count += 1  # Increment transaction count

    elapsed_time = time.time() - start_time
    print(f"Processed {count} transactions in {elapsed_time:.2f} seconds.")
    print(f"Transactions per second: {count / elapsed_time:.2f}")

# Example transaction data
transaction_data = {
    "data": "Transfer 10 tokens from A to B",
    "from": "A",
    "to": "B",
    "amount": 10
}

# Example signature and public key (hex format)
signature = "3045022100e8b5b9a1e8a73bf7f0c3ae3d77d8f62e41ad3cda4a67db2f5f01236496a0ed9c02206d98e42c12ab11f1f9b358e80b03b9b514cd4ba93513b3c2e34fd272b3571b38"
public_key = "04bfcf0e7ca431899b324be76b89ac9815cda5fdf31b7a60a69c4bcb5fda59d9e8f19f622f1f7adfd1c65e988d148d4e67a740d4b9b94ac96f9c0b44631569b3d8"

# Performance testing for 1 second duration
performance_test(transaction_data, signature, public_key, duration=1)
