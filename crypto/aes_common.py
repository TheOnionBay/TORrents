
n_rounds = 10 # Defined in the standard of AES for 128 bits key
n_columns = 4
n_rows = 4
block_size = n_columns * n_rows # Number of bytes in one message or one key

# These arrays are used as lookup tables for the result of multiplying a byte by
# 2 and 3 modulo 0x011b. We need to do these operations in mix_columns.

# Multiplying by 2 is easy, that's a binary left-shift (i << 1). But in order
# to keep the result in eight bits, we take the result modulo 0x011b. If the most
# significant bit of the input is set (if i & 0x80), then the result is bigger
# than 0x011b, and therefore we substract 0x011b from the result, as you would do
# with normal arithmetic. In our case, that means doing a XOR.
mul2 = [0 for i in range(2**8)]
for i in range(2**8):
    if i & 0x80:
        mul2[i] = (i << 1) ^ 0x011b
    else:
        mul2[i] = i << 1

# Multplying i by 3 is equal to
#   i * (1 + 2)
# = i * 1 + i * 2
# = i + i * 2
# And since the + is a binary xor, there you are
mul3 = [i ^ mul2[i] for i in range(2**8)]

def byte_mul(a, b):
    res = 0
    for i in range(8):
        if b & 1:
            res ^= a



def add_round_key(state, key):
    """Performs an addition of of two polynomials in a Gallois field of base
    two, a.k.a. XOR of input bytes.
    """
    return bytes(s ^ k for (s, k) in zip(state, key))

def expand_key(key):
    assert type(key) == bytes, "key must be of type bytes"
    assert len(key) == 16, "key must be 128 bits"
    return key * (n_rounds + 1) # TODO implement the real expand key alg
