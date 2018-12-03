
from common.encoding import json_to_bytes, bytes_to_json, file_to_payload, payload_to_file


"""
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
"""

"""
def handle_request(self, message):
    filename = message["file"]
    if filename not in self.owned_files:
        # We don't have the file, error 404 not found
        return ("File request can't be fulfilled, we don't have file " + filename, 404)

    response = {
        "type": "file",
        "file": filename,
        "data": file_to_payload(self.owned_files[filename]),
        "FSID": message["FSID"]
    }
    self.send_payload(response)
    return "ok"


def handle_receive_file(self, payload):
    self.owned_files[payload["file"]] = payload_to_file(
        os.path.join(self.default_files_path, payload["file"]), payload["data"])
    return "ok"
"""


def send_payload(payload):
    payload = json_to_bytes(payload)
    return payload.hex()


def decrypt_payload(payload):
    payload = bytes.fromhex(payload)
    return bytes_to_json(payload)

if __name__ == "__main__":
    message = {
        "type": "file",
        "file": "magritte_picture",
        "data": file_to_payload("files/a/this_is_not_a_pipe.jpg"),
        "FSID": 1234
    }
    message = send_payload(message)
    answer = decrypt_payload(message)
    payload_to_file('./files/res_magritte.jpg', answer["data"])
    print(answer["file"])
    print(answer["FSID"])
    message = {
        "type": "file",
        "file": "finding_nemo",
        "data": file_to_payload("files/a/finding_nemo.txt"),
        "FSID": 5678
    }
    message = send_payload(message)
    answer = decrypt_payload(message)
    payload_to_file('./files/res_nemo.txt', answer["data"])
    print(answer["file"])
    print(answer["FSID"])
