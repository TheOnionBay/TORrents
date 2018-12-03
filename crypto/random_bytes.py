import os

def generate_bytes(n):
    """Returns random bytes to be used 
    as an Universally Unique Identifier.
    """
    return os.urandom(n) # cryptographically secure RNG 