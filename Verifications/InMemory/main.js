const EC = require('elliptic').ec;
const axios = require('axios');
const fs = require('fs');

// Using the secp256k1 curve for ECDSA
const ec = new EC('secp256k1');

// In-memory storage for transactions
let transactions = [];

// ECDSA transaction verification function
function verifyTransaction(transactionData, signature, publicKey) {
    const key = ec.keyFromPublic(publicKey, 'hex');
    const hash = Buffer.from(transactionData); // Assuming transaction data is a string
    return key.verify(hash, signature);
}

// Sending transaction to echo server
async function sendTransactionToServer(transactionData) {
    try {
        const response = await axios.post('http://echo-server-url', transactionData);
        return response.data;
    } catch (error) {
        console.error('Error sending transaction to server:', error);
        return null;
    }
}

// Verifying received transaction from server
function verifyReceivedTransaction(receivedTransactionData, signature, publicKey) {
    return verifyTransaction(receivedTransactionData, signature, publicKey);
}

// Saving transaction to in-memory storage
function saveTransactionInMemory(transactionData) {
    transactions.push(transactionData);
}

// Example workflow to verify, send, verify again, and save
async function processTransaction(transactionData, signature, publicKey) {
    // Step 1: Verify the transaction using ECDSA
    if (!verifyTransaction(transactionData.data, signature, publicKey)) {
        console.log("Transaction verification failed.");
        return;
    }

    console.log("Transaction verified successfully.");

    // Step 2: Send transaction to the echo server and get the response
    const receivedTransaction = await sendTransactionToServer(transactionData);
    if (!receivedTransaction) {
        console.log("Failed to receive transaction from server.");
        return;
    }

    console.log("Received transaction from server:", receivedTransaction);

    // Step 3: Verify the received transaction again
    if (!verifyReceivedTransaction(receivedTransaction.data, signature, publicKey)) {
        console.log("Received transaction verification failed.");
        return;
    }

    console.log("Received transaction verified successfully.");

    // Step 4: Save the verified transaction in both in-memory and file
    saveTransactionInMemory(receivedTransaction);

    console.log("Transaction saved successfully.");
}

// Performance testing function
function performanceTest(transactionData, signature, publicKey, duration = 1) {
    const startTime = Date.now();
    let count = 0;

    // Perform verifications for the specified duration (in milliseconds)
    while (Date.now() - startTime < duration * 1000) {
        // Step 1: Verify the transaction using ECDSA
        verifyTransaction(transactionData.data, signature, publicKey);
        count++;
    }

    const elapsedTime = (Date.now() - startTime) / 1000; // Convert to seconds
    console.log(`Performed ${count} verifications in ${elapsedTime.toFixed(2)} seconds.`);
    console.log(`Verifications per second: ${(count / elapsedTime).toFixed(2)}`);
}

// Example usage:

// Example transaction data
const transactionData = {
    data: "Transfer 10 tokens from A to B",
    from: "A",
    to: "B",
    amount: 10
};

// Example signature and public key (hex format)
const signature = {
    r: "aef00c1f...",  // Replace with actual r component of the signature
    s: "b12d34e5..."   // Replace with actual s component of the signature
};

const publicKey = "04bfcf0e7c...";  // Replace with actual public key in hex

// Performance testing for 1 second duration
performanceTest(transactionData, signature, publicKey, 1);

// You can also process the transaction normally if needed
// processTransaction(transactionData, signature, publicKey);

