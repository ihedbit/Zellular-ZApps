# Decentralized Node Downtime Monitoring System

This project leverages the **Zellular Infrastructure** to implement a decentralized system for monitoring the uptime and downtime of AVS nodes. It ensures consensus among all nodes and uses Zellular sequencer for decentralized database replication.

---

## Features

1. **Operators**:
   - Each operator node exposes an endpoint to report its state (up or down).
   - Maintains a local SQLite database to record the state of other nodes.
   - Validates and logs uptime/downtime proofs from the Zellular sequencer.

2. **Aggregator**:
   - Periodically queries all operator nodes to check their status.
   - Collects signatures from operator nodes to validate suspected downtime.
   - Generates a threshold signature confirming downtime.
   - Submits the downtime logs and proofs to the Zellular sequencer.

3. **Zellular Sequencer Integration**:
   - Ensures all nodes share the same sequence of downtime/uptime events.

4. **Consensus & Decentralization**:
   - Downtime logs are validated via threshold signatures from multiple nodes.
   - Guarantees uniform state across all nodes using Zellular.

---

## Architecture

### 1. Operators
- Each operator node:
  - Hosts an API endpoint for uptime/downtime checks.
  - Stores the states of other nodes locally in a SQLite database.
  - Queries the Zellular sequencer to receive and verify downtime proofs.
  - Updates its database after verifying the proofs.

### 2. Aggregator
- The aggregator:
  - Queries operator nodes to monitor their states.
  - Randomly selects operators to validate the suspected downtime of a node.
  - Collects signatures from operators and creates a threshold signature.
  - Sends downtime logs and proofs to the Zellular sequencer.

### 3. Zellular Sequencer
- The sequencer:
  - Receives downtime logs and proofs from the aggregator.
  - Broadcasts validated proofs to all operator nodes.
  - Ensures consistency across all nodes' logs.

---

## Workflow

1. **Downtime Detection**:
   - The aggregator queries all operator nodes to check their states.
   - For any suspected downtime, the aggregator selects random operator nodes to validate the claim.
   - Collects individual signatures and generates a threshold signature.

2. **Proof Submission**:
   - The aggregator submits downtime proofs to the Zellular sequencer.
   - The sequencer broadcasts the proofs to all operator nodes.

3. **Proof Verification**:
   - Each operator receives the proofs from the sequencer.
   - Verifies the proofs and updates its local SQLite database.

4. **Consensus & Replication**:
   - All nodes maintain identical downtime/uptime logs.
   - Enables consistent queries for downtime metrics.

---

## Example Code Snippets

### Sending Downtime Proof to Zellular Sequencer
```python
zellular = zellular.Zellular("avs-liveness-checker", base_url)
zellular.send([
    {'node': 17, 'event_type': 'down', 'timestamp': 1732522695, 'sig': '0x23a3...46da'}
])
```

### Receiving and Verifying Proofs
```python
zellular = zellular.Zellular("avs-liveness-checker", base_url)
for batch, index in zellular.batches(after=index):
    events = json.loads(batch)
    for event in events:
        if verify(event):
            add_event_log(event)
```

---

## Database Example
Each operator node maintains a local SQLite database to log the downtime/uptime events of other nodes.

| Node | Timestamp                     | Duration   | Status |
|------|-------------------------------|------------|--------|
| 8    | Nov 22, 2024 00:00 - 94 h 26 min | 94 h 26 min | Up     |
| 8    | Nov 26, 2024 22:27 - 0 h 47 min | 0 h 47 min  | Down   |
| 8    | Nov 26, 2024 23:15 - 49 h 15 min | 49 h 15 min | Up     |

---

## Prerequisites

1. **Python**: Ensure Python 3.x is installed.
2. **SQLite**: Local database for each operator.
3. **Zellular SDK**: Required for sequencer communication.

---

## Setup

### 1. Clone the Repository
```bash
git clone git@github.com:ihedbit/Zellular-ZApps.git
cd DeDB
```

---

## Future Enhancements
1. Support for additional consensus mechanisms.
2. Advanced analytics for downtime trends.
3. Integration with third-party monitoring tools.

---

## Contributing
Feel free to contribute to the project by submitting issues or pull requests.

---

## License
This project is licensed under the MIT License.
