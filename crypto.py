"""Contains the encryption primitives, namely the Advanced Encryption Standard
(AES). Only the function 'encrypt' is meant to be used by the outside, all the
others are for implementation purposes and are private.

This file works with the Python type 'bytearray', which is basically a mutable
list of byte values. The message has to be of type bytearray, and the key as well,
and the key has to be 16 bytes long.
"""

n_rounds = 10 # Defined in the standard of AES for 128 bits key
n_columns = 4
n_rows = 4
block_size = n_columns * n_rows # Number of bytes in one message or one key

# These arrays are used as lookup tables for the result of multiplying a byte by
# 0x02 and 0x03 modulo 0x1b. We need to do these operations in mix_columns.

# Multiplying by 0x02 is easy, that's a binary left-shift (i << 1). But in order
# to keep the result in eight bits, we take the result modulo 0x1b. If the most
# significant bit of the input is set (if i & 0x80), then the result is bigger
# than 0x1b, and therefore we substract 0x1b from the result, as you would do
# with normal arithmetic. In our case, that means doing a XOR.
mul2 = [(i << 1) if i & 0x80 else ((i << 1) ^ 0x1b) for i in range(2**8)]

# Multplying i by 0x03 is equal to
#   i * (0x01 + 0x02)
# = i * 0x01 + i * 0x02
# = i + i * 0x02
# And since the + is a binary xor, there you are
mul3 = [i ^ mul2[i] for i in range(2**8)]

def encrypt(plain_text, key):
    assert type(plain_text) == bytearray, "plain_text must be of type bytearray"
    assert type(key) == bytearray, "key must be of type bytearray"
    assert len(key) == block_size, "key must be 128 bits"

    # Add padding to the plain text in order to have blocks of 128 bits
    plain_text = plain_text + bytearray(len(plain_text) % block_size)
    cypher_text = bytearray()

    for i in range(len(plain_text) // block_size):
        # TODO We should use another mode than using always the same cypher
        key_schedule = expand_key(key)
        plain_text_block = plain_text[i * block_size : (i + 1) * block_size]
        cypher_text += aes_encrypt_block(plain_text_block, key_schedule)

    return cypher_text

def aes_encrypt_block(plain_text, key_schedule):
    """Encrypts a message using AES-128.
    Parameters:
        plain_text: a 128 bits (16 bytes) message in byte string
        key: a 128 bits key in byte string
    """
    assert type(key_schedule) == bytearray, "key_schedule must be of type bytearray"
    assert type(plain_text) == bytearray, "plain_text must be of type bytearray"
    assert len(key_schedule) == block_size * (n_rounds + 1) "key_schedule must contain n_rounds + 1 sub-keys"
    assert len(plain_text) == block_size, "plain_text must be 128 bits"

    state = [b for b in plain_text] # Copy the message

    add_round_key(state, key_schedule[0:block_size])

    for r in range(n_rounds - 1):
        sub_bytes(state)
        shift_rows(state)
        mix_columns(state)
        state = add_round_key(state, key_schedule[(r + 1) * block_size : (r + 2) * block_size])

    sub_bytes(state)
    shift_rows(state)
    add_round_key(state, key_schedule[n_rounds * block_size : ])

    return state

def add_round_key(state, key):
    """Performs an addition of of two polynomials in a Gallois field of base
    two, a.k.a. XOR of input bytes.
    """
    for i in range(len(state)):
        state[i] ^= key[i]

def sub_bytes(state):
    # TODO do crypto stuff here

def shift_rows(state):
    # TODO do crypto stuff here

def mix_columns(state):
    for c in range(0, block_size, n_rows):
        state[c + 0] = mul2[state[c + 0]] ^ mul3[state[c + 1]] ^ state[c + 2] ^ state[c + 3]
        state[c + 0] = state[c + 0] ^ mul2[state[c + 1]] ^  mul3[state[c + 2]] ^ state[c + 3]
        state[c + 0] = state[c + 0] ^ state[c + 1] ^ mul2[state[c + 2]] ^  mul3[state[c + 3]]
        state[c + 0] = mul3[state[c + 0]] ^ state[c + 1] ^ state[c + 2] ^  mul2[state[c + 3]]

def expand_key(key):
    assert type(key) == bytearray, "key must be of type bytearray"
    assert len(key) == 16, "key must be 128 bits"
    return key * (n_rounds + 1) # TODO implement the real expand key alg
