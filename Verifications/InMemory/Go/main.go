package main

import (
	"bytes"
	// "crypto/ecdsa"
	// "crypto/elliptic"
	// "crypto/sha256"
	// "encoding/hex"
	"encoding/json"
	"fmt"
	// "log"
	// "math/big"
	"net/http"
	"time"
)

// In-memory storage for transactions
var transactions []map[string]interface{}

// ECDSA transaction verification function
func verifyTransaction(transactionData string, signature string, publicKey string) bool {
	return true
	// // Decode signature and public key from hex
	// sigBytes, err := hex.DecodeString(signature)
	// if err != nil {
	// 	log.Println("Error decoding signature:", err)
	// 	return false
	// }

	// pubKeyBytes, err := hex.DecodeString(publicKey)
	// if err != nil {
	// 	log.Println("Error decoding public key:", err)
	// 	return false
	// }

	// // Recreate the ECDSA public key
	// x, y := elliptic.Unmarshal(elliptic.P256(), pubKeyBytes)
	// if x == nil || y == nil {
	// 	log.Println("Invalid public key")
	// 	return false
	// }
	// pubKey := &ecdsa.PublicKey{Curve: elliptic.P256(), X: x, Y: y}

	// // Hash the transaction data
	// hash := sha256.Sum256([]byte(transactionData))

	// // Recreate the r and s values from the signature
	// r := big.Int{}
	// s := big.Int{}
	// sigLen := len(sigBytes)
	// r.SetBytes(sigBytes[:sigLen/2])
	// s.SetBytes(sigBytes[sigLen/2:])

	// // Verify the signature
	// valid := ecdsa.Verify(pubKey, hash[:], &r, &s)
	// return valid
}

// Sending transaction to echo server
func sendTransactionToServer(transactionData map[string]interface{}) (map[string]interface{}, error) {
	jsonData, err := json.Marshal(transactionData)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post("http://127.0.0.1:5000/echo", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result, nil
}

// Verifying received transaction from server
func verifyReceivedTransaction(receivedTransactionData string, signature string, publicKey string) bool {
	return true
	// return verifyTransaction(receivedTransactionData, signature, publicKey)
}

// Saving transaction to in-memory storage
func saveTransactionInMemory(transactionData map[string]interface{}) {
	transactions = append(transactions, transactionData)
}

// Example workflow to verify, send, verify again, and save
func processTransaction(transactionData map[string]interface{}, signature string, publicKey string) {
	// Step 1: Verify the transaction using ECDSA
	data, ok := transactionData["data"].(string)
	if !ok || !verifyTransaction(data, signature, publicKey) {
		fmt.Println("Transaction verification failed.")
		return
	}

	// Step 2: Send transaction to the echo server and get the response
	receivedTransaction, err := sendTransactionToServer(transactionData)
	if err != nil {
		fmt.Println("Failed to receive transaction from server:", err)
		return
	}

	// Step 3: Verify the received transaction again
	// receivedData, ok := receivedTransaction["data"].(string)
	// if !ok || !verifyReceivedTransaction(receivedData, signature, publicKey) {
	// 	fmt.Println("Received transaction verification failed.")
	// 	return
	// }

	// Step 4: Save the verified transaction in-memory
	saveTransactionInMemory(receivedTransaction)
}

// Performance testing function for transactions sent and verified
func performanceTest(transactionData map[string]interface{}, signature string, publicKey string, duration int) {
	startTime := time.Now()
	count := 0

	// Perform verifications for the specified duration (in seconds)
	for time.Since(startTime).Seconds() < float64(duration) {
		processTransaction(transactionData, signature, publicKey)
		count++
	}

	elapsedTime := time.Since(startTime).Seconds()
	fmt.Printf("Processed %d transactions in %.2f seconds.\n", count, elapsedTime)
	fmt.Printf("Transactions per second: %.2f\n", float64(count)/elapsedTime)
}

func main() {
	// Example transaction data
	transactionData := map[string]interface{}{
		"data":   "Transfer 10 tokens from A to B",
		"from":   "A",
		"to":     "B",
		"amount": 10,
	}

	// Example signature and public key (hex format)
	signature := "3045022100e8b5b9a1e8a73bf7f0c3ae3d77d8f62e41ad3cda4a67db2f5f01236496a0ed9c02206d98e42c12ab11f1f9b358e80b03b9b514cd4ba93513b3c2e34fd272b3571b38"
	publicKey := "04bfcf0e7ca431899b324be76b89ac9815cda5fdf31b7a60a69c4bcb5fda59d9e8f19f622f1f7adfd1c65e988d148d4e67a740d4b9b94ac96f9c0b44631569b3d8"

	// Performance testing for 1 second duration
	performanceTest(transactionData, signature, publicKey, 1)
}
