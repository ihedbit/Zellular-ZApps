// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface IAVS {
    function registerOperator(bytes calldata publicKey) external;

    function deregisterOperator() external;

    function reportDowntime(
        address targetOperator,
        uint256 timestamp,
        bytes calldata aggregatedSignature,
        bytes calldata aggregatedPublicKey
    ) external;

    function getActiveOperators() external view returns (address[] memory);
}
