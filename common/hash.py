import hashlib


def hash_payload(payload):
    m = hashlib.md5()
    m.update(payload)
    return m.digest()
