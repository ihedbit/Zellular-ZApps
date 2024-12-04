// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "./BLSUtils.sol";

contract AVS {
    using BLSUtils for bytes;

    struct Operator {
        address operatorAddress;
        bytes publicKey; // BLS public key
        bool isActive;
        uint256 lastActive; // Timestamp of the last active check
    }

    struct DowntimeReport {
        address reporter;
        address targetOperator;
        uint256 timestamp;
        bytes aggregatedSignature; // Aggregated BLS signature
        bytes aggregatedPublicKey; // Aggregated BLS public key
    }

    mapping(address => Operator) public operators;
    address[] public activeOperators;

    uint256 public constant THRESHOLD = 2; // Minimum number of valid signatures required

    event OperatorRegistered(address indexed operator, bytes publicKey);
    event OperatorDeregistered(address indexed operator);
    event DowntimeReported(address indexed reporter, address indexed targetOperator, uint256 timestamp);

    // Register an operator
    function registerOperator(bytes calldata publicKey) external {
        require(operators[msg.sender].operatorAddress == address(0), "Operator already registered");

        operators[msg.sender] = Operator({
            operatorAddress: msg.sender,
            publicKey: publicKey,
            isActive: true,
            lastActive: block.timestamp
        });

        activeOperators.push(msg.sender);

        emit OperatorRegistered(msg.sender, publicKey);
    }

    // Deregister an operator
    function deregisterOperator() external {
        require(operators[msg.sender].operatorAddress != address(0), "Operator not registered");

        operators[msg.sender].isActive = false;

        emit OperatorDeregistered(msg.sender);
    }

    // Report downtime for a target operator
    function reportDowntime(
        address targetOperator,
        uint256 timestamp,
        bytes calldata aggregatedSignature,
        bytes calldata aggregatedPublicKey
    ) external {
        require(operators[targetOperator].isActive, "Target operator not active");
        require(operators[msg.sender].isActive, "Reporter not active");

        // Verify the aggregated signature
        bytes memory message = abi.encodePacked(targetOperator, "down", timestamp);
        require(
            aggregatedSignature.verifySignature(message, aggregatedPublicKey),
            "Invalid aggregated signature"
        );

        // Update the target operator's status
        operators[targetOperator].isActive = false;

        emit DowntimeReported(msg.sender, targetOperator, timestamp);
    }

    // Get active operators
    function getActiveOperators() external view returns (address[] memory) {
        return activeOperators;
    }
}
