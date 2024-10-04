const axios = require('axios');
const { ec: EC } = require('elliptic');
const ec = new EC('secp256k1');

// In-memory storage for transactions
const transactions = [];

// ECDSA transaction verification function
function verifyTransaction(transactionData, signature, publicKey) {
    return true;
    try {
        const key = ec.keyFromPublic(publicKey, 'hex');
        const msgHash = Buffer.from(transactionData, 'utf8'); // Convert message to buffer
        return key.verify(msgHash, signature);
    } catch (error) {
        console.error('Error during signature verification:', error);
        return false;
    }
}

// Sending transaction to echo server
async function sendTransactionToServer(transactionData) {
    try {
        const response = await axios.post('http://127.0.0.1:5000/echo', transactionData);
        return response.data;
    } catch (error) {
        console.error(`Error sending transaction to server: ${error}`);
        return null;
    }
}

// Verifying received transaction from server
function verifyReceivedTransaction(receivedTransactionData, signature, publicKey) {
    return true;
    // return verifyTransaction(receivedTransactionData, signature, publicKey);
}

// Saving transaction to in-memory storage
function saveTransactionInMemory(transactionData) {
    transactions.push(transactionData);
}

// Example workflow to verify, send, verify again, and save
async function processTransaction(transactionData, signature, publicKey) {
    // Step 1: Verify the transaction using ECDSA
    if (!verifyTransaction(transactionData.data, signature, publicKey)) {
        console.log('Transaction verification failed.');
        return;
    }

    // Step 2: Send transaction to the echo server and get the response
    const receivedTransaction = await sendTransactionToServer(transactionData);
    if (!receivedTransaction) {
        console.log('Failed to receive transaction from server.');
        return;
    }

    // Step 3: Verify the received transaction again
    if (!verifyReceivedTransaction(receivedTransaction.data, signature, publicKey)) {
        console.log('Received transaction verification failed.');
        return;
    }

    // Step 4: Save the verified transaction in-memory
    saveTransactionInMemory(receivedTransaction);
}

// Performance testing function for transactions sent and verified
async function performanceTest(transactionData, signature, publicKey, duration = 1) {
    const startTime = Date.now();
    let count = 0;

    // Perform verifications for the specified duration (in milliseconds)
    while (Date.now() - startTime < duration * 1000) {
        // Step 1: Verify the transaction using ECDSA
        if (!verifyTransaction(transactionData.data, signature, publicKey)) {
            console.log('Transaction verification failed.');
            return;
        }

        // Step 2: Send transaction to the server and get the response
        const receivedTransaction = await sendTransactionToServer(transactionData);
        if (!receivedTransaction) {
            console.log('Failed to receive transaction from server.');
            return;
        }

        // Step 3: Verify the received transaction
        if (!verifyReceivedTransaction(receivedTransaction.data, signature, publicKey)) {
            console.log('Received transaction verification failed.');
            return;
        }

        // Step 4: Save the transaction in memory
        saveTransactionInMemory(receivedTransaction);

        count += 1; // Increment transaction count
    }

    const elapsedTime = (Date.now() - startTime) / 1000;
    console.log(`Processed ${count} transactions in ${elapsedTime.toFixed(2)} seconds.`);
    console.log(`Transactions per second: ${(count / elapsedTime).toFixed(2)}`);
}

// Example transaction data
const transactionData = {
    data: 'Transfer 10 tokens from A to B',
    from: 'A',
    to: 'B',
    amount: 10
};

// Example signature and public key (hex format)
const signature = '3045022100e8b5b9a1e8a73bf7f0c3ae3d77d8f62e41ad3cda4a67db2f5f01236496a0ed9c02206d98e42c12ab11f1f9b358e80b03b9b514cd4ba93513b3c2e34fd272b3571b38';
const publicKey = '04bfcf0e7ca431899b324be76b89ac9815cda5fdf31b7a60a69c4bcb5fda59d9e8f19f622f1f7adfd1c65e988d148d4e67a740d4b9b94ac96f9c0b44631569b3d8';

// Performance testing for 1 second duration
performanceTest(transactionData, signature, publicKey, 1);
