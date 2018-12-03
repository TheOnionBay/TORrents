import json

encoding = "utf-8"

def json_to_bytes(obj):
    """Returns a byte object of a given json file.
    """
    return bytes(json.dumps(obj), encoding)

def bytes_to_json(bytes_seq):
    """Returns a json object/dictionary of a given sequence of bytes.
    """
    return json.loads(bytes_seq.decode(encoding))

def file_to_payload(file_path):
    res = b""
    with open(file_path, 'rb') as file:
        for line in file:
            res += line+Rb'$$%\n'
    return res

def payload_to_file(file_path, payload):
    with open(file_path, 'wb') as file:
        for line in payload.split(Rb'$$%\n'):
            file.write(line)

