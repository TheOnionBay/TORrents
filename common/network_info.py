import json
from crypto import rsa
import os

tracker = "192.168.0.7:5000"

node_pool = [
    "192.168.0.10:5000",
    "192.168.0.11:5000",
    "192.168.0.12:5000",
    "192.168.0.13:5000",
    "192.168.0.14:5000",
    "192.168.0.15:5000",
    "192.168.0.16:5000",
    "192.168.0.17:5000",
    "192.168.0.18:5000",
    "192.168.0.19:5000",
    "192.168.0.20:5000",
]

if os.environ["DEV"] == "True":
    # Set tracker IP/port
    tracker = "127.0.0.1:5020"
    # Set nodes IP/port
    dev_node_ip = "127.0.0.1"
    dev_node_start_port = 5001
    for i in range(len(node_pool)):
        node_pool[i] = dev_node_ip + ":" + str(dev_node_start_port + i)


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
