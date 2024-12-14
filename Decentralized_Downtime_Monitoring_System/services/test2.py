import unittest
import base64
from blspy import AugSchemeMPL, PrivateKey, G1Element
from your_flask_app import sign_message, verify_message, OPERATORS

class TestSignatureVerification(unittest.TestCase):
    def setUp(self):
        # Example message
        self.message = "Test message"
        self.private_key = PrivateKey.from_seed(b"test_seed")
        self.public_key = self.private_key.get_g1()

        # Mock operators
        self.operators = {
            "operator_1_id": {
                "public_key": self.public_key.serialize().hex()
            },
        }

        global OPERATORS
        OPERATORS = self.operators

    def test_sign_message(self):
        # Sign a message
        signature = sign_message(self.message)
        
        # Ensure the signature is not None and is of type G2Element
        self.assertIsNotNone(signature)
        self.assertTrue(isinstance(signature, G1Element))

    def test_verify_message_valid(self):
        # Sign a message
        signature = sign_message(self.message)
        signature_b64 = base64.b64encode(bytes(signature)).decode('utf-8')

        # Verify the signature
        non_signers = []  # No non-signers in this test case
        aggregated_key = self.public_key
        result = verify_message(self.message, signature_b64, non_signers, aggregated_key)

        # Assert that the verification succeeds
        self.assertTrue(result)

    def test_verify_message_invalid_signature(self):
        # Use an invalid signature
        invalid_signature = base64.b64encode(b"invalid_signature").decode('utf-8')
        non_signers = []  # No non-signers in this test case
        aggregated_key = self.public_key
        result = verify_message(self.message, invalid_signature, non_signers, aggregated_key)

        # Assert that the verification fails
        self.assertFalse(result)

    def test_verify_message_with_non_signers(self):
        # Add a non-signer
        non_signer_key = PrivateKey.from_seed(b"non_signer_seed").get_g1()
        non_signer_key_hex = non_signer_key.serialize().hex()

        OPERATORS["non_signer_id"] = {"public_key": non_signer_key_hex}

        # Sign the message
        signature = sign_message(self.message)
        signature_b64 = base64.b64encode(bytes(signature)).decode('utf-8')

        # Verify with non-signers
        non_signers = ["non_signer_id"]
        aggregated_key = self.public_key + non_signer_key
        result = verify_message(self.message, signature_b64, non_signers, aggregated_key)

        # Assert that the verification fails due to incorrect aggregation
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
