Here’s the updated README with improved clarity, additional details for the rewritten scripts, and a refreshed structure:

---

# Decentralized Node Downtime Monitoring System

This project implements a **Decentralized Node Downtime Monitoring System** leveraging **Zellular Infrastructure** to achieve consensus on node uptime and downtime. It uses threshold signatures for fault tolerance and ensures a consistent state across all participating nodes.

---

## Features

1. **Operators**:
   - Hosts an API for reporting node uptime or downtime.
   - Maintains a local SQLite database to log and verify node statuses.
   - Signs and validates downtime proofs shared via the Zellular sequencer.

2. **Aggregator**:
   - Periodically monitors the statuses of all nodes.
   - Collects signatures from operator nodes to validate downtime claims.
   - Creates a threshold signature for confirmed downtime.
   - Submits validated downtime logs to the Zellular sequencer for replication.

3. **Zellular Sequencer Integration**:
   - Serves as a decentralized ledger to synchronize downtime logs across all nodes.

4. **Consensus & Decentralization**:
   - Employs threshold signatures from multiple nodes for validating downtime.
   - Guarantees identical downtime logs across all operator nodes.

---

## Architecture

### 1. Operators
- **Responsibilities**:
  - Expose APIs to report uptime/downtime.
  - Maintain logs in a SQLite database.
  - Verify downtime proofs from the aggregator.
  - Query the Zellular sequencer for validated logs.

### 2. Aggregator
- **Responsibilities**:
  - Monitor operator nodes and detect downtime.
  - Request signatures from other operators to confirm downtime.
  - Aggregate signatures into a single threshold signature.
  - Submit downtime events to the Zellular sequencer.

### 3. Zellular Sequencer
- **Responsibilities**:
  - Act as a decentralized ledger for downtime events.
  - Broadcast verified downtime logs to all operator nodes.
  - Ensure consistent replication of logs across all nodes.

---

## Workflow

### 1. **Downtime Detection**
   - The aggregator periodically checks all operator nodes for status.
   - If a node is suspected to be down, it requests validation from other nodes.
   - The aggregator collects signatures from operator nodes.

### 2. **Threshold Signature Creation**
   - The aggregator aggregates collected signatures into a threshold signature.
   - A validated downtime event is generated.

### 3. **Proof Submission**
   - The downtime proof is submitted to the Zellular sequencer.
   - The sequencer replicates the proof across all nodes.

### 4. **Proof Verification**
   - Each operator verifies the downtime proof from the sequencer.
   - Updates its local SQLite database accordingly.

---

## Updated Example Code

### Sending Downtime Proof to Zellular Sequencer
```python
event = {
    "node_id": "operator_2",
    "status": "down",
    "timestamp": 1732522695,
    "aggregated_signature": "0x23a3...46da",
    "aggregated_public_key": "0xabc1...1234",
    "signers": ["operator_1", "operator_3"]
}
zellular.send([event])
```

### Verifying and Logging Proofs
```python
for batch, index in zellular.batches(after=last_index):
    events = json.loads(batch)
    for event in events:
        if verify(event):
            log_state(event["node_id"], event["status"], event["timestamp"], event["aggregated_signature"])
```

---

## Database Schema

Each operator maintains a local SQLite database (`operator.db`) with the following schema:

| Node ID   | Timestamp           | Status  | Signature   |
|-----------|---------------------|---------|-------------|
| operator_1| 1732522695          | Down    | 0x23a3...46 |

### **Schema Definition**
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    signature TEXT NOT NULL
);
```

---

## Prerequisites

1. **Python**: Version 3.8 or above.
2. **SQLite**: Local database for operator logging.
3. **Zellular SDK**: Communication with the Zellular sequencer.

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone git@github.com:ihedbit/Zellular-ZApps.git
cd Decentralized-Node-Monitoring
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Operator
```bash
python operator.py
```

### 4. Start the Aggregator
```bash
python aggregator.py
```

---

## Example Usage

1. **Start the Operators**:
   - Run multiple `operator.py` instances on different ports (e.g., 5001, 5002).
   
2. **Start the Aggregator**:
   - Run the `aggregator.py` script to monitor operator statuses.

3. **Trigger Downtime Detection**:
   - Simulate downtime by stopping one of the operators.
   - Observe the aggregator detecting the downtime and submitting proofs to the Zellular sequencer.
---

## Contributing

Contributions are welcome! Feel free to submit issues, feature requests, or pull requests.

---

## License

This project is licensed under the MIT License.

---
