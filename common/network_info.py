import json
from crypto import rsa
import os

tracker = "127.0.0.1:5020" if os.environ['DEV'] == 'True' else "192.168.0.7"

node_pool = [
    "127.0.0.1:5001" if os.environ['DEV'] == 'True' else"192.168.0.10",
    "127.0.0.1:5002" if os.environ['DEV'] == 'True' else"192.168.0.11",
    "127.0.0.1:5003" if os.environ['DEV'] == 'True' else"192.168.0.12",
    "127.0.0.1:5004" if os.environ['DEV'] == 'True' else"192.168.0.13",
    "127.0.0.1:5005" if os.environ['DEV'] == 'True' else"192.168.0.14",
    "127.0.0.1:5006" if os.environ['DEV'] == 'True' else"192.168.0.15",
    "127.0.0.1:5007" if os.environ['DEV'] == 'True' else"192.168.0.16",
    "127.0.0.1:5008" if os.environ['DEV'] == 'True' else"192.168.0.17",
    "127.0.0.1:5009" if os.environ['DEV'] == 'True' else"192.168.0.18",
    "127.0.0.1:5010" if os.environ['DEV'] == 'True' else"192.168.0.19",
    "127.0.0.1:5011" if os.environ['DEV'] == 'True' else"192.168.0.20",
]

# For now private keys are stored here, we should decide how to create them
# and make the public keys available to the client
public_keys = json.load(open("common/public_keys.json"))
for ip, key in public_keys.items():
    public_keys[ip] = rsa.RSAPublicKey(key["n"], key["e"])

private_keys = json.load(open("common/private_keys.json"))
for ip, key in private_keys.items():
    private_keys[ip] = rsa.RSAPrivateKey(key["n"], key["d"])

cid_size = 16

# node_pool = [
#     "localhost"
# ]
