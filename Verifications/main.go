package main

import (
	"bytes"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/big"
	"net/http"
	"os"
)

// In-memory storage for transactions
var transactions []map[string]interface{}

// Transaction structure
type Transaction struct {
	Data   string `json:"data"`
	From   string `json:"from"`
	To     string `json:"to"`
	Amount int    `json:"amount"`
}

// Sending transaction to echo server
func sendTransactionToServer(transactionData map[string]interface{}) (map[string]interface{}, error) {
	data, err := json.Marshal(transactionData)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post("http://echo-server-url", "application/json", bytes.NewBuffer(data))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&result)
	if err != nil {
		return nil, err
	}
	return result, nil
}

// ECDSA transaction verification function
func verifyTransaction(transactionData string, signatureR, signatureS, pubKeyX, pubKeyY *big.Int) bool {
	hash := sha256.Sum256([]byte(transactionData))
	curve := elliptic.P256()
	pubKey := ecdsa.PublicKey{Curve: curve, X: pubKeyX, Y: pubKeyY}
	return ecdsa.Verify(&pubKey, hash[:], signatureR, signatureS)
}

// Verifying received transaction from server
func verifyReceivedTransaction(receivedTransactionData string, signatureR, signatureS, pubKeyX, pubKeyY *big.Int) bool {
	return verifyTransaction(receivedTransactionData, signatureR, signatureS, pubKeyX, pubKeyY)
}

// Saving transaction to in-memory storage
func saveTransactionInMemory(transactionData map[string]interface{}) {
	transactions = append(transactions, transactionData)
}


// Example workflow to verify, send, verify again, and save
func processTransaction(transactionData map[string]interface{}, signatureR, signatureS, pubKeyX, pubKeyY *big.Int) {
	// Step 1: Verify the transaction using ECDSA
	if !verifyTransaction(transactionData["data"].(string), signatureR, signatureS, pubKeyX, pubKeyY) {
		fmt.Println("Transaction verification failed.")
		return
	}

	fmt.Println("Transaction verified successfully.")

	// Step 2: Send transaction to the echo server and get the response
	receivedTransaction, err := sendTransactionToServer(transactionData)
	if err != nil {
		fmt.Println("Error sending transaction to server:", err)
		return
	}

	fmt.Println("Received transaction from server:", receivedTransaction)

	// Step 3: Verify the received transaction again
	if !verifyReceivedTransaction(receivedTransaction["data"].(string), signatureR, signatureS, pubKeyX, pubKeyY) {
		fmt.Println("Received transaction verification failed.")
		return
	}

	fmt.Println("Received transaction verified successfully.")

	// Step 4: Save the verified transaction in both in-memory and file
	saveTransactionInMemory(receivedTransaction)
	

	fmt.Println("Transaction saved successfully.")
}

func main() {
	// Example transaction data
	transactionData := map[string]interface{}{
		"data":   "Transfer 10 tokens from A to B",
		"from":   "A",
		"to":     "B",
		"amount": 10,
	}

	// Example signature and public key (this should be the real signature and public key)
	signatureR := big.NewInt(1234567890) // Replace with actual R value of the signature
	signatureS := big.NewInt(9876543210) // Replace with actual S value of the signature
	pubKeyX := big.NewInt(9876543210)    // Replace with actual X coordinate of the public key
	pubKeyY := big.NewInt(1234567890)    // Replace with actual Y coordinate of the public key

	// Process the transaction
	processTransaction(transactionData, signatureR, signatureS, pubKeyX, pubKeyY)
}
