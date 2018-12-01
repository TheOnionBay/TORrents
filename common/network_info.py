import json
from crypto import rsa
import os

tracker = "192.168.1.60:5000"

node_pool = [
    "192.168.1.55:5000",
    "192.168.1.55:5000",
    "192.168.1.55:5000"
]

# For now private keys are stored here, we should decide how to create them
# and make the public keys available to the client
public_keys = json.load(open("common/public_keys.json"))
for ip, key in public_keys.items():
    public_keys[ip] = rsa.RSAPublicKey(key["n"], key["e"])

private_keys = json.load(open("common/private_keys.json"))
for ip, key in private_keys.items():
    private_keys[ip] = rsa.RSAPrivateKey(key["n"], key["d"])

# Number of bytes in a Circuit IDentifier
cid_size = 16
