import unittest
from . import aes_encrypt
from . import aes_decrypt
from . import aes_common
from .random_bytes import generate_bytes

class TestAesCommon(unittest.TestCase):
    def test_expand_key(self):
        # Those test values are taken from the AES standard, Appendix A
        input = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")

        output = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c" +
                                "a0fafe1788542cb123a339392a6c7605" +
                                "f2c295f27a96b9435935807a7359f67f" +
                                "3d80477d4716fe3e1e237e446d7a883b" +
                                "ef44a541a8525b7fb671253bdb0bad00" +
                                "d4d1c6f87c839d87caf2b8bc11f915bc" +
                                "6d88a37a110b3efddbf98641ca0093fd" +
                                "4e54f70e5f5fc9f384a64fb24ea6dc4f" +
                                "ead27321b58dbad2312bf5607f8d292f" +
                                "ac7766f319fadc2128d12941575c006e" +
                                "d014f9a8c9ee2589e13f0cc8b6630ca6")

        self.assertEqual(aes_common.expand_key(input), output)

if __name__ == '__main__':
    unittest.main()
