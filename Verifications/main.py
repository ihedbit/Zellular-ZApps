import json
import requests
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError

# In-memory storage for transactions
transactions = []

# ECDSA transaction verification function
def verify_transaction(transaction_data, signature, public_key):
    vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    try:
        vk.verify(bytes.fromhex(signature), transaction_data.encode())
        return True
    except BadSignatureError:
        return False

# Sending transaction to echo server
def send_transaction_to_server(transaction_data):
    try:
        response = requests.post("http://echo-server-url", json=transaction_data)
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

# Saving transaction to a file (persistent storage)
def save_transaction_to_file(transaction_data):
    try:
        with open("transactions.txt", "a") as file:
            file.write(f"{json.dumps(transaction_data)}\n")
    except Exception as e:
        print(f"Error saving transaction to file: {e}")

# Example workflow to verify, send, verify again, and save
def process_transaction(transaction_data, signature, public_key):
    # Step 1: Verify the transaction using ECDSA
    if not verify_transaction(transaction_data['data'], signature, public_key):
        print("Transaction verification failed.")
        return
    
    print("Transaction verified successfully.")
    
    # Step 2: Send transaction to the echo server and get the response
    received_transaction = send_transaction_to_server(transaction_data)
    if not received_transaction:
        print("Failed to receive transaction from server.")
        return

    print("Received transaction from server:", received_transaction)
    
    # Step 3: Verify the received transaction again
    if not verify_received_transaction(received_transaction['data'], signature, public_key):
        print("Received transaction verification failed.")
        return
    
    print("Received transaction verified successfully.")
    
    # Step 4: Save the verified transaction in both in-memory and file
    save_transaction_in_memory(received_transaction)
    save_transaction_to_file(received_transaction)
    print("Transaction saved successfully.")

# Example transaction data
transaction_data = {
    "data": "Transfer 10 tokens from A to B",
    "from": "A",
    "to": "B",
    "amount": 10
}

# Example signature and public key (hex format)
signature = "3045022100e8b5..."  # This should be the actual signature in hex
public_key = "04bfcf0e7c..."  # This should be the actual public key in hex

# Processing the transaction
process_transaction(transaction_data, signature, public_key)
