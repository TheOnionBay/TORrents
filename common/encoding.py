import base64
import json

encoding = "utf-8"

def json_to_bytes(obj):
    return bytes(json.dumps(obj), encoding)

def bytes_to_json(bytes_seq):
    return json.loads(bytes_seq.decode(encoding))

def file_to_payload(file_path):
    res = b""
    with open(file_path, 'rb') as file:
        for line in file:
            res += line+Rb'$$%\n'
    return base64.encodebytes(res).hex()

def payload_to_file(file_path, payload):
    with open(file_path, 'wb') as file:
        for line in base64.decodebytes(bytearray.fromhex(payload)).split(Rb'$$%\n'):
            file.write(line)

