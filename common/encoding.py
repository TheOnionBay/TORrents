import json

encoding = "utf-8"

def json_to_bytes(obj):
    return bytes(json.dumps(obj), encoding)

def bytes_to_json(bytes_seq):
    return json.loads(bytes_seq.decode(encoding))

def file_to_payload(file_path):
    res = ""
    with open(file_path, 'r') as file:
        for line in file:
            res += line.strip('\n')+R'\n'
    return res

def payload_to_file(file_path, payload):
    with open(file_path, 'w') as file:
        for line in payload.split(R'\n'):
            file.write(line)

