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

# Generate the RSA key for all the nodes
# For now private keys are stored here, we should decide how to create them
# and make the public keys available to the client
public_keys = {}
private_keys = {}
for node in node_pool:
    pub, priv = generate_rsa()
    public_keys[node] = pub
    private_keys[node] = priv

cid_size = 16

# node_pool = [
#     "localhost"
# ]
