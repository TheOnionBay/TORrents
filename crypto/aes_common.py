
n_rounds = 10 # Defined in the standard of AES for 128 bits key
n_columns = 4
n_rows = 4
block_size = n_columns * n_rows # Number of bytes in one message or one key

def mul(a, b):
    """Multiplies two bytes as if they represented two binary polynomials, with
    the result taken modulo 0x11b (a constant, magic polynomial). The idea is to
    go through each bit of b, and add the value of a for every bit being set,
    and multiply a by two at every loop turn.

    For example, with b = 5:
          a * 5
        = a * (4 + 1)
        = a * 4 + a * 1
    We can see that we just add the value of a multiplied by the different
    powers of two composing b.
    """
    res = 0

    # Iterate on evey bit of b
    for i in range(8):
        # For each power of two present in b, add the current value of a
        if b & 1:
            res ^= a

        # The next four lines multiply a by 2 mod 0x11b
        if a & 0x80:
            a = (a << 1) ^ 0x011b
        else:
            a = a << 1

        # Go to the next bit in b
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
