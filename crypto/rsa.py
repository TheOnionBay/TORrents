from random import SystemRandom # cryptographically secure RNG
from math import gcd

random_gen = SystemRandom()

class RSAPublicKey:
    def __init__(self, n, e):
        self.n = n
        self.e = e

class RSAPrivateKey:
    def __init__(self, n, d):
        self.n = n
        self.d = d

def generate_rsa(key_width):
    e = 65537
    while True:
        # TODO Understand RSA
        p = random_prime(key_width // 2)
        q = random_prime(key_width // 2)
        lambda_n = lcm(p - 1, q - 1)
        if gcd(e, lambda_n) == 1:
            n = p * q
            d = mod_inverse(e, lambda_n)
            return RSAPublicKey(n, e), RSAPrivateKey(n, d)

def rsa_encrypt(plain_text, public_key):
    return exp_mod(plain_text, public_key.e, public_key.n)

def rsa_decrypt(cipher_text, private_key):
    return exp_mod(cipher_text, private_key.d, private_key.n)

def mod_inverse(a, b):
    # TODO Understand this code
    s = 0
    old_s = 1
    r = b
    old_r = a

    while r != 0:
        quotient = old_r // r
        (old_r, r) = (r, old_r - quotient * r)
        (old_s, s) = (s, old_s - quotient * s)

    return old_s % b

def lcm(a, b):
    # TODO check that
    return abs(a * b) // gcd(a, b)

def is_probably_prime(n, trials = 20):
    """Implements The Fermat Primality test. If the number n is not prime,
    the probability that this function returns True is 1/(2^trials).
    """
    for i in range(20):
        a = random_gen.randint(2, n)
        if gcd(a, n) != 1:
            return False
        if exp_mod(a, n-1, n) != 1:
            return False
    return True

def random_prime(width):
    max = (1 << width) - 1 # Equals 2^width - 1, all bit sets
    # TODO check the formula for min below
    min = 6074001000 << (width - 33) if width > 33 else int(sqrt(max))
    while True:
        res = random_gen.randint(min, max)
        if is_probably_prime(res):
            return res

def exp_mod(a, e, mod):
    product = 1
    power_of_a = None
    for i in range(e.bit_length()):
        power_of_a = (power_of_a ** 2) % mod if i > 0 else a
        if e & (1 << i):
            product *= power_of_a
    return product % mod

if __name__ == "__main__":
    pub, priv = generate_rsa(1024)
    message = 424242
    print(message)
    cipher_text = rsa_encrypt(message, pub)
    print(cipher_text)
    plain_text = rsa_decrypt(cipher_text, priv)
    print(plain_text)
