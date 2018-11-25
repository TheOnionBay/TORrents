import json

encoding = "utf-8"

def json_to_bytes(obj):
    return bytes(json.dumps(obj), encoding)

def bytes_to_json(bytes_seq):
    return json.loads(bytes_seq.decode(encoding))
