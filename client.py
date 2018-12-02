import os
import argparse
import requests
import json
from flask import Flask, render_template, request
from random import sample

from crypto.rsa import rsa_encrypt
from crypto.random_bytes import generate_bytes
from crypto.aes_encrypt import encrypt as aes_encrypt
from crypto.aes_decrypt import decrypt as aes_decrypt
from crypto import aes_common
from common.network_info import tracker, node_pool, public_keys, cid_size
from common.encoding import json_to_bytes, bytes_to_json


class Client(Flask):

    def __init__(self, name, filenames):
        super().__init__(name, template_folder=os.path.abspath('client/templates'))
        self.add_url_rule("/", "index", self.index, methods=["GET"])
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])
        self.add_url_rule("/connect", "connect", self.conn, methods=["GET"])
        self.add_url_rule("/search", "search", self.search, methods=["POST"])
        self.owned_files = json.loads(filenames)
        self.network_files = set()
        self.tunnel_nodes = []
        self.connected = False

    def run(self):
        super().run(host='0.0.0.0', use_reloader=False)

    def index(self):
        """Serves HTML page with input to request file.

        """
        data = {"owned_files": list(self.owned_files.keys()),
                "network_files": list(self.network_files),
                "connected": self.connected,
                "tunnel": self.tunnel_nodes}
        return render_template("index.html", data=data)

    def search(self):
        """Asks the tracker for the filename given in the UI form."""
        file_name = request.form["filename"] or ""
        print("Requesting file ", file_name)
        tracker_payload = {
            "type": "request",
            "file": file_name
        }
        self.send_payload(tracker_payload)

    def main_handler(self):
        """Client will receive comms from the tracker and files from other
        peers on this handler. The client can receive two types of
        messages:

        * The list of files in the network

        * A request for a sharing a file

        """
        msg = request.get_json()
        payload = self.decrypt_payload(msg["payload"])
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
        if filename not in self.owned_files:
            # We don't have the file, error 404 not found
            return ("File request can't be fulfilled, we don't have file " + filename, 404)

        response = {
            "type": "file",
            "file": filename,
            "data": self.owned_files[filename],
            "FSID": message["FSID"]
        }
        self.send_payload(response)
        return "ok"

    def handle_receive_file(self, payload):
        self.owned_files[payload["file"]] = payload["data"]
        return "ok"

    def handle_network_ls(self, files):
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
        print("I CHOSE: ", self.tunnel_nodes)
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

        requests.post("http://" + self.tunnel_nodes[0], json=message)
        self.connected = True
        return "Connected to TheOnionBay. <a href='/'>Go back</a>"

    def send_payload(self, payload):
        """Encrypts three times a message and send it to the tunnel. The
        tunnel has to be established beforehand.

        """
        payload = json_to_bytes(payload)

        # Encrypt in the reverse order, the closest node (first in the
        # list) decrypts first
        for node, sesskey in reversed(zip(self.tunnel_nodes, self.sesskeys)):
            payload = aes_encrypt(payload, sesskey)

        message = {
            "CID": self.cid,
            "payload": payload.hex()
        }

        requests.post("http://" + self.tunnel_nodes[0], json=message)

    def decrypt_payload(self, payload):
        """Peels 3 layers from the payload. Opposite routine to
        self.encrypt_payload.

        """
        payload = bytes.fromhex(payload)
        for node, sesskey in zip(self.tunnel_nodes, self.sesskeys):
            payload = aes_decrypt(payload, sesskey)

        payload = bytes_to_json(payload)
        return payload


parser = argparse.ArgumentParser(description='TORrent client')
parser.add_argument('lof', type=open, help='list of files')
args = parser.parse_args()
client = Client(__name__, args.lof.read())

client.run()
