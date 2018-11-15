
n_rounds = 10 # Defined in the standard of AES for 128 bits key
n_columns = 4
n_rows = 4
block_size = n_columns * n_rows # Number of bytes in one message or one key

def mul(a, b):
    res = 0
    for i in range(8):
        if b & 1:
            res ^= a
        if a & 0x80:
            a = (a << 1) ^ 0x011b
        else:
            a = a << 1
        b >>= 1
    return res




def add_round_key(state, key):
    """Performs an addition of of two polynomials in a Gallois field of base
    two, a.k.a. XOR of input bytes.
    """
    return bytes(s ^ k for (s, k) in zip(state, key))

def expand_key(key):
    assert type(key) == bytes, "key must be of type bytes"
    assert len(key) == 16, "key must be 128 bits"
    return key * (n_rounds + 1) # TODO implement the real expand key alg
