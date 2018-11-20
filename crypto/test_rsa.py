import unittest
import rsa
from random import randrange

class TestRsa(unittest.TestCase):
    def test_encrypt_then_decrypt(self):
        pub, priv = rsa.generate_rsa(1024)
        number_of_tests = 128
        # Generate a bunch of random messages to encrypt and then decrypt.
        # These messages have to be smaller than the modulus of the key, n.
        test_values = [randrange(0, pub.n) for _ in range(number_of_tests)]

        for test_value in test_values:
            cipher_text = rsa.rsa_encrypt(test_value, pub)
            decrypted_text = rsa.rsa_decrypt(cipher_text, priv)
            self.assertEqual(test_value, decrypted_text)

if __name__ == '__main__':
    unittest.main()
