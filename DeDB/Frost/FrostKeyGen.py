from pyfrost import FrostKeygen

num_participants = 10  # Total operators
threshold = 3          # Threshold for valid signature
keygen = FrostKeygen(num_participants=num_participants, threshold=threshold)
key_shares = keygen.generate_shares()

# Save shares for each operator and the aggregator
with open("aggregator_public_key.json", "w") as f:
    json.dump(keygen.public_key.to_dict(), f)
