import argparse
import requests
from flask import Flask, request
from midict import MIDict

from common.encoding import bytes_to_json, json_to_bytes
from common.network_info import private_keys, cid_size, tracker
from crypto.aes_encrypt import encrypt as aes_encrypt
from crypto.aes_decrypt import decrypt as aes_decrypt
from crypto import aes_common
from crypto.random_bytes import generate_bytes
from crypto.rsa import rsa_decrypt

from colorama import Fore, Back, Style
import colorama
import sys
from random import choice

class Node(Flask):

    def __init__(self, name, ip):
        super().__init__(name)
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])
        self.add_url_rule("/control/", "control_handler", self.control_handler, methods=["POST"])
        self.private_key = private_keys[ip]
        self.relay = MIDict([], ["DownIP", "DownCID", "SessKey", "UpIP", "UpCID"])
        self.up_file_transfer = MIDict([], ["FSID", "BridgeCID", "BridgeIP"])
        self.down_file_transfer = MIDict([], ["BridgeCID", "DownCID"])

        self.ip = ip
        self.colour = None
        self.colours = [Fore.YELLOW, Fore.MAGENTA, Fore.CYAN]  # Fore.RED, Fore.GREEN,
        self.statements = \
            {
                "online": "Node online at {0}",
                "incoming": "Incoming message from {0}",  # ip
                "unknownCID": "Received message with unknown CID {0}",
                "addToRelay": "Adding it to relay table with UpCID {0} and forward the message to next node at {1}",
                # ip of other node
                "forward": "CID = {0}, forwarding it {1} to {2}",  # cid , direction up/downstream ,ip of other node
                "receive_from_bridge": "Message from bridge CID {0}, forwarding it downstream to {1}",
                "transmit_to_bridge": "Transfer of file {0}, transmitting it to bridge at {1}",  # fsid, bridge ip
                "fromTracker": "Message from tracker at {0}",  # ip of tracker
                "make_bridge": "Creating bridge for {0} with CID {1} for the future file transfer of file {3}",
            # ip, cid,direction,fsid
                "receive_bridge": "Creating bridge entry for the future downstream file transfer of a file to {0} with CID {1}",
            # ip, cid

            }
        # self.cprint(.format(ip),Fore.GREEN)

    def run(self):
        self.cprint([self.ip], "online", Fore.GREEN)
        super().run(host='0.0.0.0')


    def main_handler(self):
        message = request.get_json()
        self.cprint([request.remote_addr], "incoming")
        # If the message is a file to be transmitted to a bridge
        if "FSID" in message:
            self.transmit_to_bridge(message)

        # If the message is received from a bridge, and to be transmitted down to the client
        elif message["CID"] in self.down_file_transfer.indices["BridgeCID"]:
            self.receive_from_bridge(message)

        # If the message is a normal message from down to upstream
        elif message["CID"] in self.relay.indices["DownCID"]:
            self.forward_upstream(message)

        # If the message is a response from up to downstream
        elif message["CID"] in self.relay.indices["UpCID"]:
            self.forward_downstream(message)

        # We don't know the CID of the message, we assume it contains an AES key
        else:
            self.create_tunnel(message)

        return "ok"
    def control_handler(self):
        """Tracker control messages will arrive here."""
        # Read message, update table accordingly
        message = request.get_json()
        if request.remote_addr == tracker:
            self.cprint([request.remote_addr, "fromTracker"])
            if "type" in message and message["type"] == "make_bridge":
                self.make_bridge(message["FSID"], message["bridge_CID"], message["to"])
                return "ok"
            elif "type" in message and message["type"] == "receive_bridge":
                self.receive_bridge(message["bridge_CID"], message["CID"])
                return "ok"
        return "nok"

    def transmit_to_bridge(self, message):
        if message["FSID"] not in self.up_file_transfer.indices["FSID"]:
            # We don't have file sharing data about this FSID
            return  # TODO Throw an error

        bridge_ip, bridge_cid = self.up_file_transfer["FSID": message["FSID"], ("BridgeIP", "BridgeCID")]
        self.cprint([message["FSID"], bridge_ip], "transmit_to_bridge")

        payload = {
            "type": "file",
            "file": message["file"],
            "data": message["data"]
        }
        new_message = {
            "CID": bridge_cid,
            # The payload is not encrypted, just encoded
            "payload": json_to_bytes(payload).hex()
        }
        requests.post("http://" + bridge_ip, data=new_message)
        return "ok"

    def receive_from_bridge(self, message):
        down_cid = self.down_file_transfer["BridgeCID": message["CID"], "DownCID"]
        try:
            down_ip, sess_key = self.relay["DownCID": down_cid, "DownIP"]

            self.cprint([message["CID"], down_ip], "receive_from_bridge")

            new_message = {
                "CID": down_cid,
                # Encrypt the message when sending downstream, we received it as encoded plaintext
                "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
            }
            requests.post("http://" + down_ip, data=new_message)
            return "ok"

        except KeyError:
            # If we don't have a downstream CID matching in the relay table
            return  # TODO throw an error

    def forward_upstream(self, message):
        up_cid, up_ip, sess_key = self.relay["DownCID": message["CID"], ("UpCID", "UpIP", "SessKey")]
        self.cprint([message["CID"], "upstream", up_ip], "forward")
        new_message = {
            "CID": up_cid,
            # Decrypt the payload (peel one layer of the onion)
            "payload": aes_decrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post("http://" + up_ip, data=new_message)
        return "ok"

    def forward_downstream(self, message):
        down_cid, down_ip, sess_key = self.relay["UpCID": message["CID"], ("DownCID", "DownIP", "SessKey")]

        self.cprint([message["CID"], "downstream", down_ip], "forward")

        new_message = {
            "CID": down_cid,
            # Encrypt the payload (add a layer to the onion)
            "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        request.post("http://" + down_ip, data=new_message)
        return "ok"

    def create_tunnel(self, message):
        if "aes_key" not in message:
            return  # TODO throw an error

        # Decrypt the AES key
        sess_key = rsa_decrypt(bytes.fromhex(message["aes_key"]), self.private_key)
        sess_key = sess_key[-aes_common.key_size:]  # Discard the right padding created by RSA

        # Decrypt the payload with the AES key
        # It should be a JSON string once decoded
        payload = aes_decrypt(bytes.fromhex(message["payload"]), sess_key)
        payload = bytes_to_json(payload)

        if "aes_key" not in payload or "relay" not in payload or "to" not in payload:
            # All these fields should be present
            return  # TODO throw an error

        # Generate a CID for the upstream link
        up_cid = generate_bytes(cid_size)

        self.cprint([up_cid, message["CID"]], "unknownCID")
        # Add a line to the relay table
        self.relay[:, ("DownIP", "DownCID", "SessKey", "UpIP", "UpCID")] = \
            (request.remote_addr, message["CID"], sess_key, message["to"], up_cid)

        # Forward the payload to the next node upstream
        new_message = {
            "CID": up_cid,
            # Copy verbatim the encrypted key and payload for the next node (not our business)
            "aes_key": message["aes_key"],
            "payload": message["relay"]
        }
        self.cprint([message["to"]], "addToRelay")
        requests.post("http://" + message["to"], data=new_message)
        return "ok"

    def make_bridge(self, fsid, bridge_cid, bridge_ip):
        self.cprint([bridge_ip, bridge_cid, "outgoing", fsid], "make_bridge")
        self.up_file_transfer[fsid] = (bridge_cid, bridge_ip)

    def receive_bridge(self, bridge_cid, origin_cid):
        down_cid, down_ip = self.relay["UpCID": origin_cid, ("DownCID", "DownIP")]

        self.cprint([down_ip, down_cid], "receive_bridge")
        self.down_file_transfer[bridge_cid] = (down_cid)

    def cprint(self, args, id, colour=None):
        if colour is None:
            self.colour = choice(self.colours)
            print("self.colour", self.colour)
        print(Back.BLACK + (colour or self.colour) + self.statements[id].format(*args), file=sys.stdout)


parser = argparse.ArgumentParser(description='TORrent node')
# We need the IP of the node so that it can find its own private RSA key in
# common/network_info.py
parser.add_argument('ip', type=str, help='ip address of the node')
args = parser.parse_args()
colorama.init()
node = Node(__name__, args.ip)
node.run()
