
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




"""
def handle_request(self, message):
    [. . .]
    response = {
        "type": "file",
        "file": filename,
-->     "data": file_to_payload(self.owned_files[filename]),
        "FSID": message["FSID"]
    }
    [. . .]


def handle_receive_file(self, payload):
    self.owned_files[payload["file"]] = payload_to_file(
-->     os.path.join(self.default_files_path, payload["file"]), payload["data"])
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
        "data": file_to_payload("a/this_is_not_a_pipe.jpg"),
        "FSID": 1234
    }
    message = send_payload(message)
    answer = decrypt_payload(message)
    payload_to_file('res_magritte.jpg', answer["data"])
    print(answer["file"])
    print(answer["FSID"])

    message = {
        "type": "file",
        "file": "finding_nemo",
        "data": file_to_payload("a/finding_nemo.txt"),
        "FSID": 5678
    }
    message = send_payload(message)
    answer = decrypt_payload(message)
    payload_to_file('res_nemo.txt', answer["data"])
    print(answer["file"])
    print(answer["FSID"])
