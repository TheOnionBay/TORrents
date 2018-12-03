import os
import argparse
import requests
import json
from flask import Flask, render_template, request, redirect
from random import sample
import sys

from common.hash import hash_payload
from crypto.rsa import rsa_encrypt, rsa_decrypt
from crypto.random_bytes import generate_bytes
from crypto.aes_encrypt import encrypt as aes_encrypt
from crypto.aes_decrypt import decrypt as aes_decrypt
from crypto import aes_common
from common.network_info import tracker, node_pool, public_keys, cid_size, get_url, domain_names
from common.encoding import json_to_bytes, bytes_to_json, payload_to_file, file_to_payload


class SignatureNotMatching(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class Client(Flask):

    def __init__(self, name, filenames):
        super().__init__(name, template_folder=os.path.abspath('client/templates'))
        self.add_url_rule("/", "index", self.index, methods=["GET"])
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])
        self.add_url_rule("/connect", "connect", self.conn, methods=["GET"])
        # TODO : see how to make html work with file_content
        #self.add_url_rule("/file_content", "file_content", self.file_content, methods=["GET"])
        self.add_url_rule("/disconnect", "disconnect", self.teardown, methods=["GET"])
        self.add_url_rule("/request", "request_file", self.request_file, methods=["POST"])
        self.owned_files = json.loads(filenames)
        self.default_files_path = os.path.join("client", "files")
        self.network_files = set()
        self.tunnel_nodes = []
        self.log = ""
        self.connected = False
        self.clean_files()

    def run(self):
        super().run(host='0.0.0.0', use_reloader=False)

    def file_content(self):
        print("ping")
        print(request.args)
        return self.get_content(request.args["file"])

    def get_content(self, file):
        if file.endswith(".txt"):
            text = ""
            with open(file, 'r') as f:
                for line in f:
                    text += line
            return text
        else:
            return '<img src="{}" />'.format(file)


    def clean_files(self):
        for file in os.listdir(self.default_files_path):
            if os.path.isfile(os.path.join(self.default_files_path, file)):
                os.remove(os.path.join(self.default_files_path, file))

    def index(self):
        """Serves HTML page with input to request file.

        """
        owned_text_files = {}
        owned_images = {}

        for name, file in self.owned_files.items():
            if file.lower().endswith(".jpg") or file.lower().endswith(".png"):
                owned_images[name] = file
            else:
                with open(file) as f:
                    owned_text_files[name] = f.read()
        data = {
            "owned_images": owned_images,
            "owned_text_files": owned_text_files,
            "network_files": list(self.network_files),
            "connected": self.connected,
            "tunnel": [domain_names[node] for node in self.tunnel_nodes],
            "log": self.log
        }
        return render_template("index.html", data=data)

    def request_file(self):
        """Asks the tracker for the filename given in the UI form."""
        file_name = request.form["filename"] or ""
        self.log += "Requesting file " + file_name + "\n"
        tracker_payload = {
            "type": "request",
            "file": file_name
        }
        self.send_payload(tracker_payload)
        return "File request sent. <a href='/'>Go back</a>"

    def main_handler(self):
        """Client will receive comms from the tracker and files from other
        peers on this handler. The client can receive two types of
        messages:

        * The list of files in the network

        * A request for a sharing a file

        """
        msg = request.get_json()
        self.log += "Receive message from " + msg["CID"] + "\n"
        try:
            payload = self.decrypt_payload(msg["payload"], msg["signatures"])
        except SignatureNotMatching as e:
            return str(e), 401 # 401 Not Authorized

        if payload["type"] == "request":
            return self.handle_request(payload)
        elif payload["type"] == "file":
            return self.handle_receive_file(payload)
        elif payload["type"] == "ls":
            return self.handle_network_ls(payload["files"])
        else:
            return ("Unexpected payload type", 400)

    def handle_request(self, message):
        filename = message["file"]

        self.log += "Got file request with filename " + filename + "\n"

        if filename not in self.owned_files:
            self.log += "File request can't be fulfilled\n"
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
        self.log += "Received file " + payload["file"] + "\n"
        self.owned_files[payload["file"]] = os.path.join(self.default_files_path, payload["file"])
        payload_to_file(self.owned_files[payload["file"]], payload["data"])
        return "ok"

    def handle_network_ls(self, files):
        self.log += "Received file listing from the server\n"
        self.network_files.update(files)
        return "ok"

    def select_nodes(self, node_pool):
        """Selects 3 unique public nodes from the available pool."""
        return sample(node_pool, 3)

    def conn(self):
        """Connects to the torrent network, uploading the list of files this
        client has.

        """
        self.tunnel_nodes = self.select_nodes(node_pool)
        self.sesskeys = [generate_bytes(aes_common.key_size) for _ in self.tunnel_nodes]
        self.cid = generate_bytes(cid_size).hex()

        tracker_payload = {
            "type": "ls",
            "files": list(self.owned_files.keys())
        }

        payloadZ = {
            "to": tracker,
            # The payload is plaintext between Z and the tracker, but encoded
            "relay": json_to_bytes(tracker_payload).hex()
        }

        payloadY = {
            "to": self.tunnel_nodes[2],
            # Encrypt the AES session key for Z with RSA, it will be copied by
            # the node
            "aes_key": rsa_encrypt(self.sesskeys[2], public_keys[self.tunnel_nodes[2]]).hex(),
            # Encrypt the payload for Z with the AES session key
            "relay": aes_encrypt(json_to_bytes(payloadZ), self.sesskeys[2]).hex()
        }

        payloadX = {
            "to": self.tunnel_nodes[1],
            "aes_key": rsa_encrypt(self.sesskeys[1], public_keys[self.tunnel_nodes[1]]).hex(),
            "relay": aes_encrypt(json_to_bytes(payloadY), self.sesskeys[1]).hex()
        }

        message = {
            "CID": self.cid,
            "aes_key": rsa_encrypt(self.sesskeys[0], public_keys[self.tunnel_nodes[0]]).hex(),
            "payload": aes_encrypt(json_to_bytes(payloadX), self.sesskeys[0]).hex()
        }

        requests.post(get_url(self.tunnel_nodes[0]), json=message)
        self.connected = True
        return redirect("/")

    def send_payload(self, payload):
        """Encrypts three times a message and send it to the tunnel. The
        tunnel has to be established beforehand.

        """
        payload = json_to_bytes(payload)

        # Encrypt in the reverse order, the closest node (first in the
        # list) decrypts first
        for node, sesskey in reversed(list(zip(self.tunnel_nodes, self.sesskeys))):
            payload = aes_encrypt(payload, sesskey)

        message = {
            "CID": self.cid,
            "payload": payload.hex()
        }

        requests.post(get_url(self.tunnel_nodes[0]), json=message)

    def decrypt_payload(self, payload, signatures):
        """Peels 3 layers from the payload. Opposite routine to
        self.encrypt_payload.

        """
        payload = bytes.fromhex(payload)
        for node, sesskey, signature in zip(self.tunnel_nodes, self.sesskeys, reversed(signatures)):
            payload = aes_decrypt(payload, sesskey)

            hashed_payload = hash_payload(payload)

            signature = bytes.fromhex(signature)
            decrypted_signature = rsa_decrypt(signature, public_keys[node])
            # Take the last bytes of the decrypted signature, stripping padding
            decrypted_signature = decrypted_signature[-len(hashed_payload):]

            if decrypted_signature != hashed_payload:
                self.log += "Signatures do not match for node" + domain_names[node] + "\n"
                raise SignatureNotMatching("Signatures do not match for node" + domain_names[node])

        payload = bytes_to_json(payload)
        return payload

    def teardown(self):
        payloadZ = aes_encrypt(json_to_bytes({"type": "teardown", "payload": {"type": "teardown"}}), self.sesskeys[2])
        payloadY = aes_encrypt(json_to_bytes({"type": "teardown", "payload": payloadZ}), self.sesskeys[1])
        payloadX = aes_encrypt(json_to_bytes({"type": "teardown", "payload": payloadY}), self.sesskeys[0])

        self.send_payload(payloadX)
        self.connected = False
        return redirect("/")


parser = argparse.ArgumentParser(description='TORrent client')
parser.add_argument('lof', type=open, help='list of files')
args = parser.parse_args()
client = Client(__name__, args.lof.read())

client.run()
