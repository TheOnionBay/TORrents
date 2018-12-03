import json
from crypto import rsa
import os

port = 5000

tracker = "52.209.177.56"

node_pool = [
    "18.203.186.29",
    "52.210.240.232",
    "18.202.234.48",
    "52.209.183.188",
    "54.194.238.122",
    "52.209.95.12"
]

# This is just used for clearer logging in the nodes
domain_names = {
    "18.203.186.29": "node1.theonionbay.club",
    "52.210.240.232": "node2.theonionbay.club",
    "18.202.234.48": "node3.theonionbay.club",
    "52.209.183.188": "node4.theonionbay.club",
    "54.194.238.122": "node5.theonionbay.club",
    "52.209.95.12": "node6.theonionbay.club",
    "52.209.177.56": "theonionbay.club",
    "34.246.218.29": "alice.theonionbay.club",
    "34.242.221.156": "bob.theonionbay.club"
}

def get_url(ip):
    return "http://" + ip + ":" + str(port)

# tracker = "192.168.1.60"

# node_pool = [
#     "192.168.1.11",
#     "192.168.1.12",
#     "192.168.1.19",
#     "192.168.1.3",
#     "192.168.1.55"
# ]


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
