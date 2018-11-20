from random import SystemRandom # cryptographically secure RNG
from math import gcd

random_gen = SystemRandom()

class RSAPublicKey:
    """Holds a public key for RSA encryption. This consists in two different
    integers, n and e. Both have the same bit width. This key can be shared
    publicly. It is created by generate_rsa.
    """
    def __init__(self, n, e):
        self.n = n
        self.e = e

class RSAPrivateKey:
    """Holds a private key for RSA encryption. This consists in two different
    integers, n and d. Both have the same bit width. This key has to be
    kept secret at all times. It is created by generate_rsa.
    """
    def __init__(self, n, d):
        self.n = n
        self.d = d

def generate_rsa(key_width):
    """Generates private and public RSA keys. Use the public one for
    encrypting data (with the function rsa_encrypt) and the private one to
    decrypt messages (with the function rsa_decrypt).
    """
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
    """Encrypts a message. The message has to be of type int (you can convert
    bytes to create an int value however you want) and have a value less than
    the modulus of the key (public_key.n). Therefore, this is suited to encrypt
    small messages at once.
    Parameters:
        plain_text: the message as an int, with plain_text < public_key.n
        public_key: the public key, created by generate_rsa.
    Returns:
        Another integer, the cipher text.
    """
    return exp_mod(plain_text, public_key.e, public_key.n)

def rsa_decrypt(cipher_text, private_key):
    """Decrypts a message. This is teh reverse process of rsa_encrypt.
        cipher_text: the cipher text as an int
        public_key: the public key, created by generate_rsa.
    Returns:
        The original message as when it was given to rsa_encrypt, as as int.
    """
    return exp_mod(cipher_text, private_key.d, private_key.n)

def mod_inverse(a, b):
    """Calculates the inverse of a in a ring of modulus b. That is,
    returns an integer x such that ax = 1 mod b.
    """
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
    """Returns the least common multiple of a and b."""
    # TODO check that
    return abs(a * b) // gcd(a, b)

def is_probably_prime(n, trials = 20):
    """Implements The Fermat Primality test. If the number n is not prime,
    the probability that this function returns True is 1/(2^trials).
    """
    for i in range(trials):
        a = random_gen.randint(2, n)
        if gcd(a, n) != 1:
            return False
        if exp_mod(a, n-1, n) != 1:
            return False
    return True

def random_prime(width):
    """Generate a random number which has a high probability of being
    a prime number, and has a bit length of at most width.
    """
    # We define a maximum and a minimum to pick the number, to ensure that
    # the product of two of these random primes has always at least width * 2
    # bits.
    max = (1 << width) - 1 # Equals 2^width - 1, all bit sets
    min = int(sqrt(2) * (1 << (width - 1))) # Equals sqrt(2) * 2^(width - 1)
    while True:
        res = random_gen.randint(min, max)
        if is_probably_prime(res):
            return res

def exp_mod(a, e, b):
    """Computes a to the power of e, modulo b. That could be equivalent
    to a**e % b in Python, but this naive implementation would be too slow.
    Instead, we compute the result by iterating on each bit of e, and using
    an identity of modular arithmetics:
        a^2 mod b = ((a mod b) * (a mod b)) mod b
    We use this identity to compute the value of a to all the powers of two,
    and we multiply them if the corresponding bit is present in e.
    """
    product = 1
    power_of_a = None
    for i in range(e.bit_length()):
        power_of_a = (power_of_a ** 2) % b if i > 0 else a
        if e & (1 << i):
            product *= power_of_a
    return product % b
