import time
import json
import requests
import random
import string

# Initialize balances with a Genesis Address
balance = {"GENESIS": 1000000000}
processed_transactions = []
batch_size = 100  # Number of transactions to send in one batch

# ECDSA transaction verification function (stubbed for simplicity)
def verify_transaction(transaction_data, signature, public_key):
    # Assuming all transactions are valid for this test
    return True

# Sending batch transactions to the server
def send_batch_to_server(batch_transactions):
    try:
        response = requests.post("http://127.0.0.1:8000/echo", json=batch_transactions)
        return response.json()
    except Exception as e:
        print(f"Error sending batch transactions to server: {e}")
        return None

# Adding transaction to in-memory storage and updating balances
def process_transaction(transaction_data):
    sender = transaction_data["from"]
    recipient = transaction_data["to"]
    amount = transaction_data["amount"]

    # Ensure sender has enough balance
    if balance.get(sender, 0) >= amount:
        # Update balance for sender and recipient
        balance[sender] = balance.get(sender, 0) - amount
        balance[recipient] = balance.get(recipient, 0) + amount

        # Store the processed transaction
        processed_transactions.append(transaction_data)
    else:
        print(f"Transaction from {sender} to {recipient} for {amount} tokens rejected: Insufficient balance.")

# Generate a new address
def generate_address():
    return ''.join(random.choices(string.ascii_uppercase, k=5))

# Generate sample transaction data
def generate_sample_transaction():
    sender = generate_address()
    recipient = generate_address()
    amount = random.randint(1, 100)

    # If sender doesn't exist in balance, initialize it with zero
    if sender not in balance:
        balance[sender] = 0
    if recipient not in balance:
        balance[recipient] = 0

    return {
        "data": f"Transfer {amount} tokens from {sender} to {recipient}",
        "from": sender,
        "to": recipient,
        "amount": amount
    }

# Performance testing function
def performance_test(signature, public_key, batch_size=100):
    # Step 1: Generate a batch of transactions, using the Genesis Address as the primary funder
    batch_transactions = []
    for _ in range(batch_size):
        # Use Genesis as the sender for initial transactions if needed
        transaction_data = generate_sample_transaction()
        transaction_data["from"] = "GENESIS"
        
        # Only add valid transactions with sufficient balance to the batch
        if balance["GENESIS"] >= transaction_data["amount"]:
            if verify_transaction(transaction_data['data'], signature, public_key):
                batch_transactions.append(transaction_data)

    # Step 2: Send the batch to the server
    start_time = time.time()
    response = send_batch_to_server(batch_transactions)

    # Step 3: Process each transaction in the received batch
    if response:
        for transaction in response["data"]:
            process_transaction(transaction)

    # Calculate performance
    elapsed_time = time.time() - start_time
    print(f"Processed {len(processed_transactions)} transactions in {elapsed_time:.2f} seconds.")
    print(f"Transactions per second: {len(processed_transactions) / elapsed_time:.2f}")

    # Save processed transactions and balances to a file
    with open("processed_transactions.json", "w") as file:
        json.dump(processed_transactions, file, indent=4)
    with open("balances.json", "w") as file:
        json.dump(balance, file, indent=4)

    print("Processed transactions saved to 'processed_transactions.json'.")
    print("Balances saved to 'balances.json'.")

# Example signature and public key (stubbed for simplicity)
signature = "3045022100e8b5b9a1e8a73bf7f0c3ae3d77d8f62e41ad3cda4a67db2f5f01236496a0ed9c02206d98e42c12ab11f1f9b358e80b03b9b514cd4ba93513b3c2e34fd272b3571b38"
public_key = "04bfcf0e7ca431899b324be76b89ac9815cda5fdf31b7a60a69c4bcb5fda59d9e8f19f622f1f7adfd1c65e988d148d4e67a740d4b9b94ac96f9c0b44631569b3d8"

# Run the performance test
performance_test(signature, public_key, batch_size=batch_size)
