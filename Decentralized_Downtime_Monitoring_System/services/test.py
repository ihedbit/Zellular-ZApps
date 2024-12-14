from blspy import PrivateKey, G2Element, AugSchemeMPL

# Example seeds for generating private keys
seeds = [
    b"example seed for private key generation 1",
    b"example seed for private key generation 2",
    b"example seed for private key generation 3",
    b"example seed for private key generation 4"
]

# Generate private and public keys (G2 elements)
private_keys = [AugSchemeMPL.key_gen(seed) for seed in seeds]
public_keys = [private_key.get_g1() for private_key in private_keys]

# Convert public keys to bytes and then to hex
for idx, public_key in enumerate(public_keys):
    g2_bytes = public_key.__bytes__()
    g2_hex = g2_bytes.hex()
    print(f"Public Key {idx + 1} - Size in Bytes: {len(g2_bytes)}")
    print(f"Public Key {idx + 1} - Hexadecimal: {g2_hex}")

# Aggregate the public keys
aggregated_public_key = sum(public_keys, G2Element())
aggregated_g2_bytes = aggregated_public_key.__bytes__()
aggregated_g2_hex = aggregated_g2_bytes.hex()

# Output the aggregated public key
print("\nAggregated Public Key:")
print(f"Size in Bytes: {len(aggregated_g2_bytes)}")
print(f"Hexadecimal: {aggregated_g2_hex}")
