import unittest
import crypto

class TestCrypto(unittest.TestCase):
    def test_mix_columns(self):
        # Those test values are taken from Wikipedia
        # (https://en.wikipedia.org/wiki/Rijndael_MixColumns)
        inputs = [bytearray([0xdb, 0x13, 0x53, 0x45]),
                bytearray([0xf2, 0x0a, 0x22, 0x5c]),
                bytearray([0x01, 0x01, 0x01, 0x01]),
                bytearray([0xc6, 0xc6, 0xc6, 0xc6]),
                bytearray([0xd4, 0xd4, 0xd4, 0xd5]),
                bytearray([0x2d, 0x26, 0x31, 0x4c])]

        outputs = [bytearray([0x8e, 0x4d, 0xa1, 0xbc]),
                bytearray([0x9f, 0xdc, 0x58, 0x9d]),
                bytearray([0x01, 0x01, 0x01, 0x01]),
                bytearray([0xc6, 0xc6, 0xc6, 0xc6]),
                bytearray([0xd5, 0xd5, 0xd7, 0xd6]),
                bytearray([0x4d, 0x7e, 0xbd, 0xf8])]

        for input, output in zip(inputs, outputs):
            self.assertEqual(crypto.mix_columns(input), output)

if __name__ == '__main__':
    unittest.main()