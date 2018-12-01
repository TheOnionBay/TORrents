import os
import requests
from random import sample
from flask import Flask, render_template, jsonify, request, abort
from common.network_info import cid_size
from crypto.random_bytes import generate_bytes
from threading import Timer


class Tracker(Flask):

    to_value = 60

    def __init__(self):
        super().__init__(__name__, template_folder=os.path.abspath('tracker/templates'))
        self.add_url_rule("/", "index", self.index, methods=["GET"])
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])

        self.files = {"movie1": {"cid1"},
                      "movie2": {"cid2"},
                      "movie3": {"cid3"}}

        self.peers = {"cid1": "IP1",
                      "cid2": "IP2"}

        self.timeouts = {"cid1": True,
                        }
        self.fsid_counter = 0

        self.check_timeouts()

    def index(self):
        # Process list of files a client has
        return render_template("index.html",
                               data={"file_list": list(self.files.keys()),
                                     "peers": self.peers})

    def check_timeouts(self):
        for key, value in self.timeouts.items():
            if not value:
                self.remove_cid(key)
            else:
                self.timeouts[key] = False

        Timer(Tracker.to_value, self.check_timeouts).start()

    def remove_cid(self, cid):
        for file, origin in self.files:
            if cid in origin:
                self.files[file].remove(cid)
                if not self.files[file]:
                    self.remove_file(file)
        del self.peers[cid]
        del self.timeouts[cid]

    def remove_file(self, file):
        del self.files[file]

    def main_handler(self):
        message = request.get_json()
        self.timeouts[message["CID"]] = True

        if message["payload"]["type"] == "ping":
            return "ok"
        # A new client connects to the network by sending the list of files
        elif message["payload"]["type"] == "ls":
            return self.handle_new_client(message["CID"], request.remote_addr, message["payload"]["files"])

        # A client sends a file request, this is the only other possibility
        else:
            if message["payload"]["type"] != "request":
                return ("Unexpected payload type", 400)

            return self.handle_file_request(message["CID"], message["payload"]["file"])

    def handle_new_client(self, cid, ip, files):
        """
        Registers a new client by remembering the CID and IP of the exit node,
        and send back the list of available files.
        """
        # Add the IP address
        self.peers[cid] = ip
        # Add the list of files
        for file in files:
            if file not in self.files:
                self.files[file] = set()
            self.files[file["name"]].add(cid)

        # Send back the list of files
        response = {
            "CID": cid,
            "payload": {
                "type": "ls",
                "files": list(self.files.keys())
            }
        }
        url = "http://" + ip
        requests.post(url, json=response)
        return "ok"

    def handle_file_request(self, request_client_cid, file):
        """
        Checks availability of the requested file and creates a bridge if
        available.
        """
        if file not in self.files:
            abort(404)

        request_client_ip = self.peers[request_client_cid]

        # Find the CID and IP of the client owning the requested file
        owning_client_cid = sample(self.files[file], 1)[0]
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
        requests.post("http://" + owning_client_ip + "/control/", json=make_bridge_message)

        # Send a message to the node at the end of the bridge
        receive_bridge_message = {
            "type": "receive_bridge",
            "CID": request_client_cid,
            "bridge_CID": bridge_cid
        }
        # Send on the control channel of the node
        requests.post("http://" + request_client_ip + "/control/", json=receive_bridge_message)

        # Send a message to the client, asking he/she to send the file
        request_message = {
            "CID": owning_client_cid,
            "payload": {
                "type": "request",
                "file": file,
                "FSID": fsid
            }
        }
        requests.post("http://" + request_client_ip, json=request_message)
        return "ok"

tracker = Tracker()
tracker.run(host='0.0.0.0')
