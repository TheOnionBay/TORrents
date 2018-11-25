import unittest
from crypto import aes_encrypt
from crypto import aes_decrypt
from crypto import aes_common
from crypto.random_bytes import generate_bytes

class TestAesEncrypt(unittest.TestCase):
    def test_encrypt_then_decrypt(self):
        # Generate a random key
        key = generate_bytes(aes_common.key_size)
        number_of_tests = 128
        # Generate a bunch of random messages to encrypt and then decrypt.
        test_values = [generate_bytes(aes_common.block_size) for _ in range(number_of_tests)]

        for i, test_value in enumerate(test_values):
            cipher_text = aes_encrypt.encrypt(test_value, key)
            decrypted_text = aes_decrypt.decrypt(cipher_text, key)
            self.assertEqual(test_value, decrypted_text)

    def test_mix_columns(self):
        # Those test values are taken from the AES standard, Appendix C.1
        inputs = [bytes.fromhex("6353e08c0960e104cd70b751bacad0e7"),
                bytes.fromhex("a7be1a6997ad739bd8c9ca451f618b61"),
                bytes.fromhex("3bd92268fc74fb735767cbe0c0590e2d"),
                bytes.fromhex("2d6d7ef03f33e334093602dd5bfb12c7"),
                bytes.fromhex("36339d50f9b539269f2c092dc4406d23"),
                bytes.fromhex("e8dab6901477d4653ff7f5e2e747dd4f"),
                bytes.fromhex("b458124c68b68a014b99f82e5f15554c"),
                bytes.fromhex("3e1c22c0b6fcbf768da85067f6170495"),
                bytes.fromhex("54d990a16ba09ab596bbf40ea111702f")]

        outputs = [bytes.fromhex("5f72641557f5bc92f7be3b291db9f91a"),
                bytes.fromhex("ff87968431d86a51645151fa773ad009"),
                bytes.fromhex("4c9c1e66f771f0762c3f868e534df256"),
                bytes.fromhex("6385b79ffc538df997be478e7547d691"),
                bytes.fromhex("f4bcd45432e554d075f1d6c51dd03b3c"),
                bytes.fromhex("9816ee7400f87f556b2c049c8e5ad036"),
                bytes.fromhex("c57e1c159a9bd286f05f4be098c63439"),
                bytes.fromhex("baa03de7a1f9b56ed5512cba5f414d23"),
                bytes.fromhex("e9f74eec023020f61bf2ccf2353c21c7"),
                bytes.fromhex("ff87968431d86a51645151fa773ad009")]

        for input, output in zip(inputs, outputs):
            self.assertEqual(aes_encrypt.mix_columns(input), output)

    def test_shift_rows(self):
        inputs = [bytes.fromhex("63cab7040953d051cd60e0e7ba70e18c"),
                  bytes.fromhex("a761ca9b97be8b45d8ad1a611fc97369"),
                  bytes.fromhex("3b59cb73fcd90ee05774222dc067fb68"),
                  bytes.fromhex("2dfb02343f6d12dd09337ec75b36e3f0"),
                  bytes.fromhex("36400926f9336d2d9fb59d23c42c3950"),
                  bytes.fromhex("e847f56514dadde23f77b64fe7f7d490"),
                  bytes.fromhex("b415f8016858552e4bb6124c5f998a4c"),
                  bytes.fromhex("3e175076b61c04678dfc2295f6a8bfc0"),
                  bytes.fromhex("5411f4b56bd9700e96a0902fa1bb9aa1")]

        outputs = [bytes.fromhex("6353e08c0960e104cd70b751bacad0e7"),
                  bytes.fromhex("a7be1a6997ad739bd8c9ca451f618b61"),
                  bytes.fromhex("3bd92268fc74fb735767cbe0c0590e2d"),
                  bytes.fromhex("2d6d7ef03f33e334093602dd5bfb12c7"),
                  bytes.fromhex("36339d50f9b539269f2c092dc4406d23"),
                  bytes.fromhex("e8dab6901477d4653ff7f5e2e747dd4f"),
                  bytes.fromhex("b458124c68b68a014b99f82e5f15554c"),
                  bytes.fromhex("3e1c22c0b6fcbf768da85067f6170495"),
                  bytes.fromhex("54d990a16ba09ab596bbf40ea111702f")]

        for input, output in zip(inputs, outputs):
            self.assertEqual(aes_encrypt.shift_rows(input), output)

    def test_encrypt_block(self):
        # Values taken from the AES standard, Appendix C
        plain_text = bytes.fromhex("00112233445566778899aabbccddeeff")
        key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        key = aes_common.expand_key(key)
        cipher_text = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
        self.assertEqual(aes_encrypt.aes_encrypt_block(plain_text, key), cipher_text)

if __name__ == '__main__':
    unittest.main()
