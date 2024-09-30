# Token Transfer System Using Zellular Sequencer

This document outlines a token transfer system implemented using Zellular for decentralized consensus and sequencing. The system allows users to securely transfer tokens between accounts, with Zellular ensuring the correct order and finality of transactions.

## 1. Introduction

In this system, each user begins with a predefined balance, and they can transfer tokens to other users by submitting transactions to the Zellular sequencer. Zellular ensures that all transactions are handled in a secure and fault-tolerant manner by finalizing transactions in the correct order.

This document provides an overview of the system’s architecture, API endpoints, Zellular integration, and signature verification.

### 2. System Architecture

- **Flask**: Serves as the framework for implementing the API.
- **SQLite**: Used for storing user balances.
- **Zellular**: A decentralized sequencer used to ensure Byzantine Fault Tolerance (BFT) and correct transaction sequencing.
- **ECDSA**: Provides cryptographic signature verification to ensure secure transfers.

### 3. How It Works

#### Token Transfer Overview
Each user has a public/private key pair. To initiate a transfer, the sender signs a transaction that includes the recipient’s public key and the amount to transfer. The signed transaction is sent to the Zellular sequencer, which ensures that it is properly ordered and finalized.

#### Zellular Sequencing and Consensus
Zellular ensures that all transactions are processed in the correct order and finalizes them in a decentralized manner. Once a transaction is finalized by Zellular, the system updates the balances of the sender and the recipient in the local SQLite database.

### 4. API Endpoints

#### `/transfer` (POST)
This endpoint allows users to initiate a token transfer.

##### Parameters:
- **public_key**: The public key of the sender (base64 encoded).
- **recipient**: The public key of the recipient (base64 encoded).
- **amount**: The amount of tokens to transfer.
- **signature**: The cryptographic signature of the transaction (base64 encoded).

##### Example Request:

```bash
POST /transfer HTTP/1.1
Content-Type: application/x-www-form-urlencoded

public_key=<sender_public_key>&recipient=<recipient_public_key>&amount=1000&signature=<signed_transaction>
```

##### Example Response:

```json
{
  "success": true
}
```

If the signature is invalid or the sender has insufficient balance, the request will fail.

##### Error Responses:
- **403 Forbidden**: If the signature is invalid or if the sender has insufficient tokens.

### 5. Zellular Sequencer Integration

The system sends each token transfer to the Zellular sequencer to ensure the transaction is included in the correct order. The following example shows how a transaction is submitted to the sequencer:

```python
data = {
    'transactions': [{'public_key': sender_public_key, 'recipient': recipient_public_key, 'amount': amount}],
    'timestamp': int(time.time())
}
requests.put(f"{base_url}/node/{app_name}/batches", json=data, headers=headers)
```

The Zellular sequencer finalizes the transaction and ensures that all participants have the same view of the transaction order. The balances of the sender and recipient are only updated after Zellular has finalized the transaction.

### 6. Signature Verification

To ensure that only valid transactions are processed, the system uses ECDSA with the SECP256k1 curve for signature verification. Each transaction is signed by the sender using their private key, and the signature is verified against the sender’s public key before processing.

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

Once Zellular finalizes a transaction, the system updates the balances of both the sender and recipient. The sender’s balance is reduced, and the recipient’s balance is increased by the amount of tokens transferred.

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

The system continuously polls the Zellular sequencer to retrieve finalized transactions. Once transactions are finalized, they are processed to update the user balances.

```python
def process_loop():
    verifier = zellular.Verifier(app_name, base_url)
    for batch, index in verifier.batches(after=0):
        txs = json.loads(batch)
        for tx in txs:
            process_transfer(tx)
```

### 9. Running the System

To run the system, ensure that the Zellular sequencer is running and configured properly. Afterward, start the Flask application to begin processing transactions. The system will automatically retrieve finalized transactions from the Zellular sequencer.

```bash
python app.py
```

### 10. Conclusion

This token transfer system demonstrates how to integrate Zellular to sequence and finalize transactions in a decentralized and secure manner. Using Zellular ensures that all token transfers are properly ordered, verified, and finalized in a fault-tolerant way. This system can be expanded with additional features such as token minting, multi-signature wallets, and decentralized exchanges.
