import pytest
import requests
import base64
from blspy import G1Element, G2Element, AugSchemeMPL
from aggregator import query_node_status, collect_signatures, aggregate_signatures, aggregate_public_keys
from operator import sign_message

# Mock Data
NODE_URL = "http://127.0.0.1:5001"
MOCK_OPERATORS = {
    "operator_1": {
        "socket": "http://127.0.0.1:5001",
        "public_key": "abcd1234..."  # Replace with actual public key (hex)
    },
    "operator_2": {
        "socket": "http://127.0.0.1:5002",
        "public_key": "efgh5678..."  # Replace with actual public key (hex)
    },
}

# Unit Tests for Aggregator
def test_query_node_status():
    """Test querying a node's status."""
    response = query_node_status(NODE_URL)
    assert "node_id" in response
    assert "status" in response
    assert "timestamp" in response

def test_collect_signatures(monkeypatch):
    """Test collecting signatures from other operators."""
    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return {
                    "node_id": "operator_1",
                    "status": "up",
                    "timestamp": 1234567890,
                    "signature": base64.b64encode(b"mock_signature").decode()
                }
        return MockResponse()
    monkeypatch.setattr(requests, "post", mock_post)
    signatures, signers = collect_signatures(NODE_URL)
    assert len(signatures) > 0
    assert len(signers) > 0

def test_aggregate_signatures():
    """Test aggregating multiple signatures."""
    mock_signatures = [{"signature": base64.b64encode(b"mock_sig").decode()}]
    agg_sig = aggregate_signatures(mock_signatures)
    assert agg_sig is not None

def test_aggregate_public_keys():
    """Test aggregating public keys."""
    mock_signers = ["operator_1", "operator_2"]
    agg_pub_key = aggregate_public_keys(mock_signers)
    assert agg_pub_key is not None

# Unit Tests for Operator
def test_operator_status():
    """Test the operator's status endpoint."""
    response = requests.get(f"{NODE_URL}/status")
    assert response.status_code == 200
    json_data = response.json()
    assert "node_id" in json_data
    assert "status" in json_data
    assert "timestamp" in json_data

def test_operator_check_node(monkeypatch):
    """Test the operator's check_node endpoint."""
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return {
                    "node_id": "operator_2",
                    "status": "up",
                    "timestamp": 1234567890
                }
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    response = requests.post(f"{NODE_URL}/check_node", json={"node_url": "http://127.0.0.1:5002"})
    assert response.status_code == 200
    json_data = response.json()
    assert "node_id" in json_data
    assert "status" in json_data
    assert "signature" in json_data

def test_operator_sign_message():
    """Test message signing."""
    message = "test_message"
    signature = sign_message(message)
    assert isinstance(signature, G2Element)

# Integration Test
def test_integration(monkeypatch):
    """Test the full flow from aggregator to operator."""
    # Mock operator responses
    def mock_get_status(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return {
                    "node_id": "operator_1",
                    "status": "down",
                    "timestamp": 1234567890
                }
        return MockResponse()

    def mock_post_check_node(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return {
                    "node_id": "operator_2",
                    "status": "down",
                    "timestamp": 1234567890,
                    "signature": base64.b64encode(b"mock_signature").decode()
                }
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get_status)
    monkeypatch.setattr(requests, "post", mock_post_check_node)

    # Simulate aggregator process
    target_status = query_node_status(NODE_URL)
    assert target_status["status"] == "down"
    signatures, signers = collect_signatures(NODE_URL)
    agg_sig = aggregate_signatures(signatures)
    agg_pub_key = aggregate_public_keys(signers)
    assert agg_sig is not None
    assert agg_pub_key is not None
