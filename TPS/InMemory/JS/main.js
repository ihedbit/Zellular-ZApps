const axios = require('axios');
const fs = require('fs');

// Initialize balances with a Genesis Address
let balance = { "GENESIS": 1000000000 };
let processedTransactions = [];
const batchSize = 100;  // Number of transactions to send in one batch

// ECDSA transaction verification function (stubbed for simplicity)
function verifyTransaction(transactionData, signature, publicKey) {
    // Assuming all transactions are valid for this test
    return true;
}

// Sending batch transactions to the server
async function sendBatchToServer(batchTransactions) {
    try {
        const response = await axios.post("http://127.0.0.1:8000/echo", batchTransactions);
        return response.data;
    } catch (error) {
        console.error("Error sending batch transactions to server:", error);
        return null;
    }
}

// Adding transaction to in-memory storage and updating balances
function processTransaction(transactionData) {
    const sender = transactionData.from;
    const recipient = transactionData.to;
    const amount = transactionData.amount;

    // Ensure sender has enough balance
    if ((balance[sender] || 0) >= amount) {
        // Update balance for sender and recipient
        balance[sender] = (balance[sender] || 0) - amount;
        balance[recipient] = (balance[recipient] || 0) + amount;

        // Store the processed transaction
        processedTransactions.push(transactionData);
    } else {
        console.log(`Transaction from ${sender} to ${recipient} for ${amount} tokens rejected: Insufficient balance.`);
    }
}

// Generate a new address
function generateAddress() {
    return Array.from({ length: 5 }, () => String.fromCharCode(65 + Math.floor(Math.random() * 26))).join('');
}

// Generate sample transaction data
function generateSampleTransaction() {
    const sender = generateAddress();
    const recipient = generateAddress();
    const amount = Math.floor(Math.random() * 100) + 1;

    // If sender doesn't exist in balance, initialize it with zero
    if (!(sender in balance)) balance[sender] = 0;
    if (!(recipient in balance)) balance[recipient] = 0;

    return {
        data: `Transfer ${amount} tokens from ${sender} to ${recipient}`,
        from: sender,
        to: recipient,
        amount: amount
    };
}

// Performance testing function
async function performanceTest(signature, publicKey, batchSize = 100) {
    // Step 1: Generate a batch of transactions, using the Genesis Address as the primary funder
    const batchTransactions = [];
    for (let i = 0; i < batchSize; i++) {
        // Use Genesis as the sender for initial transactions if needed
        const transactionData = generateSampleTransaction();
        transactionData.from = "GENESIS";
        
        // Only add valid transactions with sufficient balance to the batch
        if (balance["GENESIS"] >= transactionData.amount) {
            if (verifyTransaction(transactionData.data, signature, publicKey)) {
                batchTransactions.push(transactionData);
            }
        }
    }

    // Step 2: Send the batch to the server
    const startTime = Date.now();
    const response = await sendBatchToServer(batchTransactions);

    // Step 3: Process each transaction in the received batch
    if (response && response.data) {
        response.data.forEach(transaction => processTransaction(transaction));
    }

    // Calculate performance
    const elapsedTime = (Date.now() - startTime) / 1000;
    console.log(`Processed ${processedTransactions.length} transactions in ${elapsedTime.toFixed(2)} seconds.`);
    console.log(`Transactions per second: ${(processedTransactions.length / elapsedTime).toFixed(2)}`);

    // Save processed transactions and balances to files
    fs.writeFileSync("processed_transactions.json", JSON.stringify(processedTransactions, null, 4));
    fs.writeFileSync("balances.json", JSON.stringify(balance, null, 4));

    console.log("Processed transactions saved to 'processed_transactions.json'.");
    console.log("Balances saved to 'balances.json'.");
}

// Example signature and public key (stubbed for simplicity)
const signature = "sample_signature";
const publicKey = "sample_public_key";

// Run the performance test
performanceTest(signature, publicKey, batchSize);
