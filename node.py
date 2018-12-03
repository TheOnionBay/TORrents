import traceback
import os
import argparse
import requests
from flask import Flask, request, render_template
from midict import MIDict

from common.encoding import bytes_to_json, json_to_bytes
from common.network_info import private_keys, cid_size, tracker, domain_names, get_url
from crypto.aes_encrypt import encrypt as aes_encrypt
from crypto.aes_decrypt import decrypt as aes_decrypt
from crypto import aes_common
from crypto.random_bytes import generate_bytes
from crypto.rsa import rsa_decrypt

from colorama import Fore, Back
import colorama
import sys
from random import choice


class Node(Flask):

    def __init__(self, name, ip):
        super().__init__(name, template_folder=os.path.abspath('node/templates'))
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])
        self.add_url_rule("/", "index", self.index, methods=["GET"])
        self.add_url_rule("/control", "control_handler", self.control_handler, methods=["POST"])
        self.private_key = private_keys[ip]
        self.up_relay = {}
        self.down_relay = {}
        self.up_file_transfer = {}
        self.down_file_transfer = {}

        self.ip = ip
        self.colour = None
        self.log = ""
        self.colours = [Fore.YELLOW, Fore.MAGENTA, Fore.CYAN]  # Fore.RED, Fore.GREEN,
        self.statements = \
            {
                "online": "Node online at {0}",
                "incoming": "\n -->Incoming message from {0}",  # ip
                "cid": "The message has CID {0}",
                "unknownCID": "Received message with unknown CID {0}",
                "add_to_relay": "Adding it to relay table with UpCID {0} and forward the message to next node at {1}",
                # ip of other node
                "forward": "CID = {0}, forwarding it {1} to {2}",  # cid , direction up/downstream ,ip of other node
                "receive_from_bridge": "Message from bridge CID {0}, forwarding it downstream to {1}",
                "transmit_to_bridge": "Transfer of file {0}, transmitting it to bridge at {1}",  # fsid, bridge ip
                "fromTracker": "\n Control message from tracker at {0}",  # ip of tracker
                "make_bridge": "Creating bridge for {0} with CID {1} for the future file transfer of file {3}",
                # ip, cid,direction,fsid
                "receive_bridge": "Creating bridge entry for the future downstream file transfer of a file to {0} with CID {1}",
                # ip, cid
            }
        # self.cprint(.format(ip),Fore.GREEN)

    def run(self):
        self.cprint([self.ip], "online", Fore.GREEN)
        super().run(host='0.0.0.0', use_reloader=False)

    def index(self):
        """GET method on /. Displays node UI
        """
        data = {"ip": domain_names[self.ip],
                "log": self.log}

        return render_template("index.html", data=data)

    def main_handler(self):
        message = request.get_json()
        from_ip = request.remote_addr

        colour = choice(self.colours)
        self.cprint([from_ip], "incoming", colour)
        self.cprint([message["CID"]], "cid", colour)

        # If the message is received from a bridge, and to be
        # transmitted down to the client
        if message["CID"] in self.down_file_transfer:
            return self.receive_from_bridge(message, colour)

        # If the message is a normal message from down to upstream or
        # to a bridge
        elif message["CID"] in self.down_relay.keys():
            return self.forward_upstream(message, colour)

        # If the message is a response from up to downstream
        elif message["CID"] in self.up_relay.keys():
            return self.forward_downstream(message, colour)

        # We don't know the CID of the message, we assume it contains
        # an AES key
        elif "aes_key" in message:
            return self.create_tunnel(message, colour)

        else:
            return "Unknown kind of message", 400 # 400 Bad Request

    def control_handler(self):
        """Tracker control messages will arrive here. The table is update
        accordingly

        """
        message = request.get_json()
        from_ip = request.remote_addr
        colour = choice(self.colours)
        #if from_ip != tracker:
            #return "control messages only allowed from the tracker", 405 # 405 Method Not Allowed
        self.cprint([from_ip], "fromTracker", colour)
        if "type" in message and message["type"] == "make_bridge":
            return self.make_bridge(message["FSID"], message["bridge_CID"], message["to"], colour)
        elif "type" in message and message["type"] == "receive_bridge":
            return self.receive_bridge(message["bridge_CID"], message["CID"], colour)

    def matching_cid_ip_from_down(self, cid, fromip):
        return fromip == self.down_relay[cid]["DownIP"]

    def matching_cid_ip_from_up(self, cid, fromip):
        return fromip == self.up_relay[cid]["UpIP"]

    def bridgeCID_matches_existing_downCID(self, bridgeCID):
        down_cid = self.down_file_transfer[bridgeCID]
        return down_cid in self.down_relay.keys()

    def transmit_to_bridge(self, payload, colour):
        fsid = payload["FSID"]
        # Disabled for now, this test causes problems
        #if fsid not in self.up_file_transfer:
            #return "FSID not found for file sharing", 404 # 404 Not Found

        bridge_ip = self.up_file_transfer[fsid]["IP"]
        bridge_cid = self.up_file_transfer[fsid]["CID"]
        self.cprint([fsid, bridge_ip], "transmit_to_bridge", colour)

        new_message = {
            "CID": bridge_cid,
            # The payload is not encrypted, just encoded
            "payload": json_to_bytes({
                "type": "file",
                "file": payload["file"],
                "data": payload["data"]
            }).hex()
        }
        print("SENDING MESSAGE TO BRIDGE:")
        print(new_message)
        requests.post(get_url(bridge_ip), json=new_message)
        return "ok"

    def receive_from_bridge(self, message, colour):
        # Disabled check for now, it may cause problems
        #if not self.bridgeCID_matches_existing_downCID(message["CID"])
            #return "Bridge CID does not matches with a down CID", 400 # 400 Bad Request

        down_cid = self.down_file_transfer[message["CID"]]

        down_ip = self.down_relay[down_cid]["DownIP"]
        sess_key = self.down_relay[down_cid]["SessKey"]

        self.cprint([message["CID"], down_ip], "receive_from_bridge", colour)

        new_message = {
            "CID": down_cid,
            # Encrypt the message when sending downstream, we
            # received it as encoded plaintext
            "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post(get_url(down_ip), json=new_message)
        return "ok"


    def forward_upstream(self, message, colour):
        up_cid = self.down_relay[message["CID"]]["UpCID"]
        up_ip = self.down_relay[message["CID"]]["UpIP"]
        sess_key = self.down_relay[message["CID"]]["SessKey"]

        # Decrypt the payload (peel one layer of the onion)
        payload = aes_decrypt(bytes.fromhex(message["payload"]), sess_key)

        # Try to decode the payload
        try:
            decoded_payload = bytes_to_json(payload)
            # No decoding exception, the payload was a valid JSON once
            # decoded.

            # Two possibilities here: the payload is for a bridge or
            # for the tracker
            print(decoded_payload)
            if "FSID" in decoded_payload:
                return self.transmit_to_bridge(decoded_payload, colour)
            # If we pass here, then we should just forward upstream
        except:
            # A decoding exception occurred, just forward upstream
            print("Unexpected error:", sys.exc_info()[0])
            print("MEssage: ", message)
            print("Decrypted payload:", payload)
            print(traceback.format_exc())

        self.cprint([message["CID"], "upstream", up_ip], "forward", colour)
        new_message = {
            "CID": up_cid,
            "payload": payload.hex()
        }
        requests.post(get_url(up_ip), json=new_message)
        return "ok"

    def forward_downstream(self, message, colour):
        down_cid = self.up_relay[message["CID"]]["DownCID"]
        down_ip = self.up_relay[message["CID"]]["DownIP"]
        sess_key = self.up_relay[message["CID"]]["SessKey"]


        self.cprint([message["CID"], "downstream", down_ip], "forward", colour)

        new_message = {
            "CID": down_cid,
            # Encrypt the payload (add a layer to the onion)
            "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post(get_url(down_ip), json=new_message)
        return "ok"

    def create_tunnel(self, message, colour):
        # Decrypt the AES key
        sess_key = rsa_decrypt(bytes.fromhex(message["aes_key"]), self.private_key)
        sess_key = sess_key[-aes_common.key_size:]  # Discard the right padding created by RSA

        # Decrypt the payload with the AES key
        # It should be a JSON string once decoded
        payload = aes_decrypt(bytes.fromhex(message["payload"]), sess_key)
        payload = bytes_to_json(payload)

        if "relay" not in payload or "to" not in payload:
            # All these fields should be present
            return "relay and to are needed in payload when creating the tunnel", 400 # 400 Bad Request

        # Generate a CID for the upstream link
        up_cid = generate_bytes(cid_size).hex()

        self.cprint([message["CID"]], "unknownCID", colour)
        # Add info to the relay tables
        self.down_relay[message["CID"]] = {"DownIP": request.remote_addr,
                                           "SessKey": sess_key,
                                           "UpCID": up_cid,
                                           "UpIP": payload["to"]}

        self.up_relay[up_cid] = {"DownCID": message["CID"],
                                 "DownIP": request.remote_addr,
                                 "SessKey": sess_key,
                                 "UpIP": payload["to"]}

        # Forward the payload to the next node upstream
        new_message = {
            "CID": up_cid,
            # Copy verbatim the encrypted key and payload for the next
            # node (not our business)
            "payload": payload["relay"]
        }
        if "aes_key" in payload:
            new_message["aes_key"] = payload["aes_key"]

        self.cprint([up_cid, payload["to"]], "add_to_relay", colour)
        requests.post(get_url(payload["to"]), json=new_message)
        return "ok"

    def make_bridge(self, fsid, bridge_cid, bridge_ip, colour):
        self.cprint([bridge_ip, bridge_cid, "outgoing", fsid], "make_bridge",colour)
        self.up_file_transfer[fsid] = {"IP": bridge_ip, "CID": bridge_cid}
        return "ok"

    def receive_bridge(self, bridge_cid, origin_cid, colour):
        down_cid = self.up_relay[origin_cid]["DownCID"]
        down_ip = self.up_relay[origin_cid]["DownIP"]

        self.cprint([down_ip, down_cid], "receive_bridge", colour)
        self.down_file_transfer[bridge_cid] = down_cid
        return "ok"

    def cprint(self, args, id, colour):
        # Replace IPs by their domain names whenever possible in args
        for i in range(len(args)):
            if args[i] in domain_names:
                args[i] = domain_names[args[i]]

        self.log += self.statements[id].format(*args)
        self.log += "\n"
        print(Back.BLACK + colour + self.statements[id].format(*args), file=sys.stdout)


parser = argparse.ArgumentParser(description='TORrent node')
# We need the IP of the node so that it can find its own private RSA
# key in the network info files.
parser.add_argument('ip', type=str, help='ip address of the node')
args = parser.parse_args()
colorama.init(autoreset=True)
node = Node(__name__, args.ip)
node.run()
