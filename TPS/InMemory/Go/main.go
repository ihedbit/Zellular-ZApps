package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "log"
    "math/rand"
    "net/http"
    "time"
)

var balance = map[string]int{"GENESIS": 1000000000}
var processedTransactions []Transaction
const batchSize = 100

type Transaction struct {
    Data   string `json:"data"`
    From   string `json:"from"`
    To     string `json:"to"`
    Amount int    `json:"amount"`
}

// ECDSA transaction verification function (stubbed for simplicity)
func verifyTransaction(transactionData, signature, publicKey string) bool {
    return true
}

// Send batch transactions to server
func sendBatchToServer(batchTransactions []Transaction) []Transaction {
    jsonData, _ := json.Marshal(batchTransactions)
    resp, err := http.Post("http://127.0.0.1:8000/echo", "application/json", bytes.NewBuffer(jsonData))
    if err != nil {
        log.Println("Error sending batch transactions to server:", err)
        return nil
    }
    defer resp.Body.Close()

    var response []Transaction
    err = json.NewDecoder(resp.Body).Decode(&response)
    if err != nil {
        log.Println("Error decoding server response:", err)
        return nil
    }
    return response
}

// Process transaction and update balances
func processTransaction(transaction Transaction) {
    sender, recipient, amount := transaction.From, transaction.To, transaction.Amount

    if balance[sender] >= amount {
        balance[sender] -= amount
        balance[recipient] += amount
        processedTransactions = append(processedTransactions, transaction)
    } else {
        fmt.Printf("Transaction from %s to %s for %d tokens rejected: Insufficient balance.\n", sender, recipient, amount)
    }
}

// Generate new address
func generateAddress() string {
    letters := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result := make([]byte, 5)
    for i := range result {
        result[i] = letters[rand.Intn(len(letters))]
    }
    return string(result)
}

// Generate sample transaction data
func generateSampleTransaction() Transaction {
    sender, recipient := generateAddress(), generateAddress()
    amount := rand.Intn(100) + 1

    if _, ok := balance[sender]; !ok {
        balance[sender] = 0
    }
    if _, ok := balance[recipient]; !ok {
        balance[recipient] = 0
    }

    return Transaction{
        Data:   fmt.Sprintf("Transfer %d tokens from %s to %s", amount, sender, recipient),
        From:   sender,
        To:     recipient,
        Amount: amount,
    }
}

// Performance testing function
func performanceTest(signature, publicKey string) {
    batchTransactions := []Transaction{}
    for i := 0; i < batchSize; i++ {
        transaction := generateSampleTransaction()
        transaction.From = "GENESIS"

        if balance["GENESIS"] >= transaction.Amount {
            if verifyTransaction(transaction.Data, signature, publicKey) {
                batchTransactions = append(batchTransactions, transaction)
            }
        }
    }

    start := time.Now()
    response := sendBatchToServer(batchTransactions)

    if response != nil {
        for _, transaction := range response {
            processTransaction(transaction)
        }
    }

    elapsed := time.Since(start).Seconds()
    fmt.Printf("Processed %d transactions in %.2f seconds.\n", len(processedTransactions), elapsed)
    fmt.Printf("Transactions per second: %.2f\n", float64(len(processedTransactions))/elapsed)

    saveToFile("processed_transactions.json", processedTransactions)
    saveToFile("balances.json", balance)
}

func saveToFile(filename string, data interface{}) {
    jsonData, _ := json.MarshalIndent(data, "", "  ")
    _ = ioutil.WriteFile(filename, jsonData, 0644)
}

// Main function
func main() {
    rand.Seed(time.Now().UnixNano())
    signature, publicKey := "sample_signature", "sample_public_key"
    performanceTest(signature, publicKey)
}
