import os

def generate_bytes(n):
    return os.urandom(n) # cryptographically secure RNG 
