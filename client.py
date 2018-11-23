
import os
import requests
import json
import argparse
from flask import Flask, render_template
from random import sample
from crypto.random_bytes import generate_bytes

from common.network_info import tracker, node_pool


class Client(Flask):

    def __init__(self, name, filenames):
        super().__init__(name, template_folder=os.path.abspath('client/templates'))
        self.fl = self.file_list(filenames)
        self.tunnel_nodes = self.select_nodes(node_pool)
        self.sesskeys = []

    def file_list(self, file):
        """Parses the JSON document containing the list of files for this
        client
        """
        return json.loads(file)

    def select_nodes(self, node_pool):
        """Selects 3 public nodes from the available pool
        """
        return sample(node_pool, 3)

    def conn(self):
        """Connect to the torrent network, uploading the list of files this
        client has.
        """
        self.sesskeys.append(generate_bytes(16))
        self.sesskeys.append(generate_bytes(16))
        self.sesskeys.append(generate_bytes(16))
        cid = generate_bytes(16)
        tracker_payload = self.fl

        payloadZ = {
                    "aes_key": self.sesskeys[2].hex(),
                    "to": tracker,
                    "relay": bytes(json.dumps(tracker_payload), 'ascii').hex()
                    }

        payloadY = {
                    "aes_key": self.sesskeys[1].hex(),
                    "to": self.tunnel_nodes[2],
                    "relay": bytes(json.dumps(payloadZ), 'ascii').hex()
                    }

        payloadX = {
                   "aes_key": self.sesskeys[0].hex(),
                   "to": self.tunnel_nodes[1],
                   "relay": bytes(json.dumps(payloadY), 'ascii').hex()
                   }

        message = {
                   "CID": cid.hex(),
                   "payload": bytes(json.dumps(payloadX), 'ascii').hex()
                   }

        r = requests.post("http://" + self.tunnel_nodes[0], data=message)

    def request_file(self, file_name):
        """Asks for the file to the tracker
        """
        print("Request the file: ", file_name)
        pass

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


@client.route("/", methods=['GET'])
def index():
    # Serve HTML page with input to request file
    # Make a request for the available files to download, for now just passing a the same files of the clinet
    return render_template("index.html", data=client.fl)


@client.route("/", methods=['POST'])
def main_handler():
    """Client will receive comms from the tracker and files from other
    peers on this handler
    """
    # Unencrypt request with keys available, max 3 times !
    pass


@client.route("/request/<file_name>", methods=['POST'])
def request(file_name):
    # Get filename wanted
    file_name = file_name or ""
    print("Request File: ", file_name)
    client.request_file(file_name)
    return (''), 204


client.run()
client.conn()
