
n_rounds = 10 # Defined in the standard of AES for 128 bits key
block_size = 16 # Number of bytes in one message or one key

def aes_encrypt_block(plain_text, key_schedule):
    """Encrypts a message using AES-128.
    Parameters:
        plain_text: a 128 bits (16 bytes) message in byte string
        key: a 128 bits key in byte string
    """
    assert type(key_schedule) == bytes, "key_schedule must be of type bytes"
    assert type(plain_text) == bytes, "plain_text must be of type bytes"
    assert len(key_schedule) == block_size * (n_rounds + 1) "key_schedule must contain n_rounds + 1 sub-keys"
    assert len(plain_text) == block_size, "plain_text must be 128 bits"

    state = [b for b in plain_text] # Copy the message

    state = add_round_key(state, key_schedule[0:block_size])

    for r in range(n_rounds - 1):
        state = sub_bytes(state)
        state = shift_rows(state)
        state = mix_columns(state)
        state = add_round_key(state, key_schedule[(r + 1) * block_size : (r + 2) * block_size])

    state = sub_bytes(state)
    state = shift_rows(state)
    state = add_round_key(state, key_schedule[n_rounds * block_size : ])

    return state

def add_round_key(state, key):
    """Performs an addition of of two polynomials in a Gallois field of base
    two, a.k.a. XOR of input bytes.
    """
    return bytes(s ^ k for s, k in zip(state, key))

def sub_bytes(state):
    return state # TODO do crypto stuff here

def shift_rows(state):
    return state # TODO do crypto stuff here

def mix_columns(state):
    return state # TODO do crypto stuff here

def expand_key(key):
    assert type(key) == bytes, "key must be of type bytes"
    assert len(key) == 16, "key must be 128 bits"
    return key * (n_rounds + 1) # TODO implement the real expand key alg

def encrypt(plain_text, key):
    assert type(plain_text) == bytes, "plain_text must be of type bytes"
    assert type(key) == bytes, "key must be of type bytes"
    assert len(key) == block_size, "key must be 128 bits"

    # Add padding to the plain text in order to have blocks of 128 bits
    plain_text = plain_text + bytes(len(plain_text) % block_size)
    cypher_text = bytes()

    for i in range(len(plain_text) // message_size):
        # TODO We should use another mode than using always the same cypher
        key_schedule = expand_key(key)
        plain_text_block = plain_text[i * block_size : (i + 1) * block_size]
        cypher_text += aes_encrypt_block(plain_text_block, key_schedule)

    return cypher_text
