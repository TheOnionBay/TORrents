import os
import requests
from flask import Flask, render_template, jsonify, request
from common.network_info import cid_size
from crypto.random_bytes import generate_bytes


class Tracker(Flask):
    def __init__(self):
        super().__init__(__name__, template_folder=os.path.abspath('tracker/templates'))

        self.files = {"movie1": "cid1",
                 "movie2": "cid2",
                 "movie3": "cid3"}

        self.peers = {"cid1": "IP1",
                 "cid2": "IP2"}

        self.fsid_counter = 0

    def handle_message(self, message):
        # A new client connects to the network by sending the list of files
        if message["payload"]["type"] == "ls":
            self.handle_new_client(message["CID"], request.remote_addr, message["payload"]["files"])

        # A client sends a file request, this is the only other possibility
        else:
            if message["payload"]["type"] != "request":
                return # TODO return an error code or something

            self.handle_file_request(message["CID"], message["payload"]["file"])


    def handle_new_client(self, cid, ip, files):
        """
        Registers a new client by remembering the CID and IP of the exit node,
        and send back the list of available files.
        """
        # Add the IP address
        self.peers[cid] == ip

        # Add the list of files
        for file in files:
            self.files[file["name"]] = cid

        # Send back the list of files
        response = {
            "CID": cid,
            "payload": {
                "type": "ls",
                "files": list(self.files.keys())
            }
        }
        requests.post(ip, data=response)

    def handle_file_request(self, request_client_cid, file):
        """
        Checks availability of the requested file and creates a bridge if
        available.
        """
        if file not in self.files:
            return # TODO return an error code or something

        request_client_ip = self.peers[request_client_cid]

        # Find the CID and IP of the client owning the requested file
        owning_client_cid = self.files[file]
        owning_client_ip = self.peers[owning_client_cid]

        # Create the CID and FSID for this bridge
        bridge_cid = generate_bytes(cid_size)
        fsid = self.fsid_counter
        self.fsid_counter += 1

        # Send a message to the node at the start of the bridge
        make_bridge_message = {
            "type": "make_bridge",
            "bridge_CID": bridge_cid,
            "to": request_client_ip,
            "FSID": fsid
        }
        # Send on the control channel of the node
        requests.post(owning_client_IP + "/control/", data=make_bridge_message)

        # Send a message to the node at the end of the bridge
        receive_bridge_message = {
            "type": "receive_bridge",
            "CID": request_client_cid,
            "bridge_CID": bridge_cid
        }
        # Send on the control channel of the node
        requests.post(request_client_ip + "/control/", data=receive_bridge_message)

        # Send a message to the client, asking he/she to send the file
        request_message = {
            "CID": owning_client_CID,
            "payload": {
                "type": "request",
                "file": file,
                "FSID": fsid
            }
        }
        requests.post(request_client_ip, data=request_message)

tracker = Tracker()

@tracker.route("/", methods=['POST'])
def main_handler():
    message = request.get_json()
    tracker.handle_message(message)

@tracker.route("/", methods=['GET'])
def index():
    # Process list of files a client has
    return render_template("index.html",
                           data={"file_list": list(files.keys()),
                                 "peers": peers})

tracker.run(host='0.0.0.0')
