import unittest
import rsa
from random_bytes import generate_bytes

class TestRsa(unittest.TestCase):
    def test_encrypt_then_decrypt(self):
        pub, priv = rsa.generate_rsa()
        number_of_tests = 128
        # Generate a bunch of random messages to encrypt and then decrypt.
        test_values = [generate_bytes(rsa.max_message_length) for _ in range(number_of_tests)]

        for test_value in test_values:
            cipher_text = rsa.rsa_encrypt(test_value, pub)
            decrypted_text = rsa.rsa_decrypt(cipher_text, priv)
            self.assertEqual(test_value, decrypted_text)

if __name__ == '__main__':
    unittest.main()
