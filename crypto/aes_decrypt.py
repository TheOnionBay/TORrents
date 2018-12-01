from .aes_common import *
from collections import deque

def decrypt(cipher_text, key):
    assert type(cipher_text) == bytes, "cipher_text must be of type bytes"
    assert len(cipher_text) % block_size == 0, "cipher_text must consist of a whole number of blocks"
    assert type(key) == bytes, "key must be of type bytes"
    assert len(key) == block_size, "key must be 128 bits"

    res = bytes()
    key_schedule = expand_key(key)
    # Extract the init vector from the start of the cipher text
    init_vector = cipher_text[:block_size]
    cipher_text = cipher_text[block_size:]
    previous_cipher_text = init_vector

    for i in range(len(cipher_text) // block_size):
        block = cipher_text[i * block_size : (i + 1) * block_size]
        # Decrypt using Cipher Block Chaining (CBC) mode
        plain_text_block = aes_decrypt_block(block, key_schedule)
        plain_text_block = xor(previous_cipher_text, plain_text_block)
        previous_cipher_text = block
        res += plain_text_block

    res = res.strip(b'\x00')

    return res

def aes_decrypt_block(cipher_text, key_schedule):
    """Decrypts a message using AES-128.
    Parameters:
        cipher_text: a 128 bits (16 bytes) encrypted message in byte string
        key: a 128 bits key in byte string
    """
    assert type(key_schedule) == bytes, "key_schedule must be of type bytes"
    assert type(cipher_text) == bytes, "cipher_text must be of type bytes"
    assert len(key_schedule) == block_size * (n_rounds + 1), "key_schedule must contain n_rounds + 1 sub-keys"
    assert len(cipher_text) == block_size, "cipher_text must be 128 bits"

    state = [b for b in cipher_text] # Copy the message

    # Add the last key first
    state = add_round_key(state, key_schedule[n_rounds * block_size : (n_rounds + 1) * block_size])

    # Use the keys in descending order
    for r in range(n_rounds - 1, 0, -1):
        state = inv_shift_rows(state)
        state = inv_sub_bytes(state)
        state = add_round_key(state, key_schedule[r * block_size : (r + 1) * block_size])
        state = inv_mix_columns(state)

    state = inv_shift_rows(state)
    state = inv_sub_bytes(state)
    # Now add the first key
    state = add_round_key(state, key_schedule[:block_size])

    return state

def inv_sub_bytes(state):
    return bytes(inv_s_box[s] for s in state)

def inv_shift_rows(state):
    array = []
    for r in range(n_rows):
        array.append(deque([]))

    count = 0
    for j in range(n_columns):
        for i in range(n_rows):
            array[i].append(state[count])
            count += 1
    for i in range(n_rows):
        array[i].rotate(i)

    state = []
    for j in range(n_columns):
        for i in range(n_rows):
            state.append(array[i][j])

    return bytes(state)

def inv_mix_columns(state):
    res = bytearray(len(state))
    for c in range(0, len(state), n_rows):
        res[c + 0] = mul(14, state[c + 0]) ^ mul(11, state[c + 1]) ^ mul(13, state[c + 2]) ^ mul(9,  state[c + 3])
        res[c + 1] = mul(9,  state[c + 0]) ^ mul(14, state[c + 1]) ^ mul(11, state[c + 2]) ^ mul(13, state[c + 3])
        res[c + 2] = mul(13, state[c + 0]) ^ mul(9,  state[c + 1]) ^ mul(14, state[c + 2]) ^ mul(11, state[c + 3])
        res[c + 3] = mul(11, state[c + 0]) ^ mul(13, state[c + 1]) ^ mul(9,  state[c + 2]) ^ mul(14, state[c + 3])
    return bytes(res)
