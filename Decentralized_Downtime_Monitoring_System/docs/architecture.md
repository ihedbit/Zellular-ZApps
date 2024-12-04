# AVS Architecture

## Overview
The Active Validation Service (AVS) is a decentralized system designed for monitoring and validating the activity of operators in a blockchain network. It utilizes BLS signatures for efficient aggregation and verification.

## Components
- **Smart Contracts**: Handle registration, downtime reporting, and validation logic.
- **Operator Service**: Runs on individual nodes to report and verify states.
- **Aggregator Service**: Collects and aggregates downtime proofs and submits them to the AVS contract.
- **Zellular Integration**: Ensures efficient interaction with the sequencer.

## Workflow
1. **Registration**: Operators register with their BLS public keys.
2. **Monitoring**: Operators monitor their peers and report downtime.
3. **Verification**: Aggregated BLS signatures validate downtime claims.
4. **Incentives**: Honest operators are rewarded, and downtime penalties are enforced.

---
