Aggregator Code (aggregator.py)

This script represents the aggregator that:

    Queries operator nodes to check their statuses.
    Collects signatures and generates a threshold signature.
    Sends the downtime logs and proofs to the Zellular sequencer.

How It Works

    Operator:
        Hosts an API to respond to status queries (/status) and accept updates from other nodes (/update_state).
        Maintains a SQLite database to log the states of other nodes.

    Aggregator:
        Periodically queries all operators to check their statuses.
        If a node is down, collects signatures from other nodes about the downtime.
        Creates a downtime event and submits it to the Zellular sequencer.

    Database:
        The operator uses SQLite to maintain logs for all downtime and uptime events.

    Zellular Sequencer:
        Receives downtime proofs from the aggregator and broadcasts them to all nodes (mocked here for simplicity).