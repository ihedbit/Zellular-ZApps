
# Token Transfer System Using Zellular Sequencer

This document outlines a simple token transfer system implemented using Zellular for consensus and sequencing. The system allows users to transfer tokens between each other in a secure and decentralized manner.

## 1. Introduction

In this implementation, each user starts with a default balance of 10 tokens. Users can transfer tokens to other users using their public keys. The transfer of tokens is processed through the Zellular sequencer, which ensures that transactions are handled in a secure, fault-tolerant, and decentralized way.

This guide walks through the implementation details, including the API endpoints, Zellular integration, and signature verification.

### 2. System Architecture

- **Flask**: Used to implement the API that users interact with.
- **SQLite**: Used for storing user balances.
- **Zellular**: A decentralized sequencer is used to achieve Byzantine Fault Tolerance (BFT) and ensure the correct order of transactions.
- **ECDSA**: Used to verify signatures for secure token transfers.

### 3. How It Works

#### Token Transfer Overview
Each user has a public/private key pair. Users can transfer tokens by signing a transaction that includes the recipient’s public key and the amount to be transferred. The transaction is forwarded to the Zellular sequencer for consensus and finalization.

#### Consensus Using Zellular
Zellular ensures the correct ordering of transactions and that all participants have a consistent view of finalized transactions. Once the sequencer finalizes a transaction, it updates the balances of the sender and recipient in the local SQLite database.

### 4. API Endpoints

#### `/transfer` (POST)
This endpoint allows users to initiate a token transfer.

##### Parameters:
- **public_key**: The public key of the sender (base64 encoded).
- **recipient**: The public key of the recipient (base64 encoded).
- **amount**: The amount of tokens to be transferred.
- **signature**: The signature of the transaction (base64 encoded).

##### Example Request:

```bash
POST /transfer HTTP/1.1
Content-Type: application/x-www-form-urlencoded

public_key=<sender_public_key>&recipient=<recipient_public_key>&amount=5&signature=<signed_transaction>
```

##### Example Response:

```json
{
  "success": true
}
```

The request will fail if the signature is invalid or if the sender does not have enough tokens.

##### Error Responses:
- **403 Forbidden**: If the signature is invalid or if the sender has insufficient tokens.

### 5. Zellular Sequencer Integration

The system integrates with the Zellular sequencer to ensure transaction order and finality. After a user initiates a transfer, the transaction is sent to the Zellular sequencer via a `PUT` request.

```python
data = {
    'transactions': [{'public_key': sender_public_key, 'recipient': recipient_public_key, 'amount': amount}],
    'timestamp': int(time.time())
}
requests.put(zsequencer_url, json=data, headers=headers)
```

The Zellular sequencer processes the transaction and returns a finalized result. Once the transaction is finalized, the system updates the balances for the sender and recipient.

### 6. Signature Verification

The system uses ECDSA with the SECP256k1 curve for signature verification. Each transaction is signed by the sender using their private key. The system verifies the transaction by checking the signature against the sender's public key.

```python
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
```

### 7. Balance Updates

Once a transaction is finalized, the balances of the sender and recipient are updated:

```python
def process_transfer(transaction):
    sender_balance = Balance.query.filter_by(public_key=sender_public_key).first()
    recipient_balance = Balance.query.filter_by(public_key=recipient_public_key).first()

    if not sender_balance or sender_balance.amount < amount:
        print(f"Error: insufficient funds for {sender_public_key}")
        return

    sender_balance.amount -= amount
    if recipient_balance:
        recipient_balance.amount += amount
    else:
        new_recipient_balance = Balance(public_key=recipient_public_key, amount=amount)
        db.session.add(new_recipient_balance)

    db.session.commit()
```

### 8. Polling the Zellular Sequencer

The system continuously polls the Zellular sequencer for finalized transactions. Finalized transactions are then processed to update user balances.

```python
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
        print(f"Received finalized indexes: [{sorted_numbers[0]}, ..., {sorted_numbers[-1]}]")

        for tx in finalized_txs:
            process_transfer(tx)
```

### 9. Running the System

To run the system, ensure that you have Zellular running as a sequencer and then start the Flask application. The application will automatically begin processing transactions once they are finalized by Zellular.

```bash
python app.py
```

### 10. Conclusion

This simple token transfer system demonstrates how Zellular can be integrated to sequence and finalize transactions in a decentralized manner. By using Zellular for consensus, we ensure fault tolerance and correctness in token transfers. The system can be expanded to include more complex features, such as token minting, multi-signature wallets, or decentralized exchanges.
