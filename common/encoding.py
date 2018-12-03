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
