import requests
import json
import argparse
from flask import Flask, render_template
from random import sample

from crypto.rsa import rsa_encrypt, rsa_decrypt
from crypto.random_bytes import generate_bytes
from crypto.aes_encrypt import encrypt as aes_encrypt
from crypto.aes_decrypt import decrypt as aes_decrypt
from crypto import aes_common
from common.network_info import tracker, node_pool, public_keys, cid_size
from common.encoding import json_to_bytes, bytes_to_json
import os


class Client(Flask):

    def __init__(self, name, filenames):
        super().__init__(name, template_folder=os.path.abspath('client/templates'))
        self.add_url_rule("/", "index", self.index, methods=["GET"])
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])
        self.add_url_rule("/request/<file_name>", "request_handler", self.request_handler, methods=["POST"])
        self.file_list = json.loads(filenames)

    def run(self):
        #self.conn()
        super().run(host='0.0.0.0')

    def index(self):
        # Serve HTML page with input to request file
        # Make a request for the available files to download, for now just passing a the same files of the clinet
        return render_template("index.html", data=client.file_list)


    def main_handler(self):
        """Client will receive comms from the tracker and files from other
        peers on this handler. The client can receive two types of messages:
        * The list of files in the network
        * A request for a sharing a file
        """
        # Unencrypt request with keys available, max 3 times !
        pass

    def request_handler(self, file_name):
        # Get filename wanted
        file_name = file_name or ""
        print("Request File: ", file_name)
        tracker_payload = {
            "type": "request",
            "file": file_name
        }
        self.send_payload(tracker_payload)
        return (''), 204

    def select_nodes(self, node_pool):
        """Selects 3 public nodes from the available pool."""
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
            "files": self.file_list
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

        r = requests.post("http://" + self.tunnel_nodes[0], data=message)

    def send_payload(self, payload):
        """Encrypts three times a message and send it to the tunnel.
        The tunnel has to be established beforehand.
        """
        payload = json_to_bytes(payload)

        # Encrypt in the reverse order, the closest node (first in the list) decrypts first
        for node, sesskey in reversed(zip(self.tunnel_nodes, self.sesskeys)):
            payload = aes_encrypt(payload, sesskey)

        message = {
            "CID": self.cid,
            "payload": payload.hex()
        }

        r = requests.post(self.tunnel_nodes[0], data=message)

    def client_loop(self):
        """This function makes the client interactive and puts the terminal in
        a read-eval loop where the input + newline is considered the file
        this client is requesting to the tracker/torrent
        """
        # read eval loop from stdin
        # send request
        pass


parser = argparse.ArgumentParser(description='TORrent client')
parser.add_argument('lof', type=open, help='list of files')
args = parser.parse_args()
client = Client(__name__, args.lof.read())
client.run()
