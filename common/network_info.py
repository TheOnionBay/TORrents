import json

tracker = "192.168.0.7"

node_pool = [
    "192.168.0.10",
    "192.168.0.11",
    "192.168.0.12",
    "192.168.0.13",
    "192.168.0.14",
    "192.168.0.15",
    "192.168.0.16",
    "192.168.0.17",
    "192.168.0.18",
    "192.168.0.19",
    "192.168.0.20",
]

# For now private keys are stored here, we should decide how to create them
# and make the public keys available to the client
public_keys = json.load(open("common/public_keys.json"))
private_keys = json.load(open("common/private_keys.json"))

cid_size = 16

# node_pool = [
#     "localhost"
# ]
