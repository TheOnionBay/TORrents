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

from colorama import Fore, Back
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
                "add_to_relay": "Adding it to relay table with UpCID {0} and forward the message to next node at {1}",
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
        super().run(host='0.0.0.0', use_reloader=False)

    def main_handler(self):
        print(self.relay)
        message = request.get_json()
        print(message)
        from_ip = request.remote_addr + ":5000"

        colour=choice(self.colours)
        self.cprint([from_ip], "incoming",colour)
        # If the message is a file to be transmitted to a bridge
        if "FSID" in message:
            print("IFCASE: File for the bridge")
            self.transmit_to_bridge(message,colour)

        # If the message is received from a bridge, and to be transmitted down to the client
        elif message["CID"] in self.down_file_transfer.indices["BridgeCID"]:
            print("IFCASE: Received from bridge, transmitting down")
            self.receive_from_bridge(message,colour)

        # If the message is a normal message from down to upstream
        elif message["CID"] in self.relay.indices["DownCID"]:
            print("IFCASE: Normal message")
            self.forward_upstream(message,colour)

        # If the message is a response from up to downstream
        elif message["CID"] in self.relay.indices["UpCID"]:
            print("IFCASE: ")
            self.forward_downstream(message,colour)

        # We don't know the CID of the message, we assume it contains an AES key
        else:
            print("IFCASE: I have to create tunnel !")
            self.create_tunnel(message,colour)

        return "ok"

    def control_handler(self):
        """Tracker control messages will arrive here. The table is update
        accordingly

        """
        message = request.get_json()
        from_ip = request.remote_addr + ":5000"
        colour = choice(self.colours)
        if from_ip == tracker:
            self.cprint([from_ip, "fromTracker"],colour)
            if "type" in message and message["type"] == "make_bridge":
                self.make_bridge(message["FSID"], message["bridge_CID"], message["to"],colour)
                return "ok"
            elif "type" in message and message["type"] == "receive_bridge":
                self.receive_bridge(message["bridge_CID"], message["CID"],colour)
                return "ok"
        return "nok"

    def transmit_to_bridge(self, message,colour):
        if message["FSID"] not in self.up_file_transfer.indices["FSID"]:
            # We don't have file sharing data about this FSID
            return  # TODO Throw an error

        bridge_ip, bridge_cid = self.up_file_transfer["FSID": message["FSID"], ("BridgeIP", "BridgeCID")]
        self.cprint([message["FSID"], bridge_ip], "transmit_to_bridge",colour)

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
        requests.post("http://" + bridge_ip, json=new_message)
        return "ok"

    def receive_from_bridge(self, message,colour):
        down_cid = self.down_file_transfer["BridgeCID": message["CID"], "DownCID"]
        try:
            down_ip, sess_key = self.relay["DownCID": down_cid, "DownIP"]

            self.cprint([message["CID"], down_ip], "receive_from_bridge",colour)

            new_message = {
                "CID": down_cid,
                # Encrypt the message when sending downstream, we received it as encoded plaintext
                "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
            }
            requests.post("http://" + down_ip, json=new_message)
            return "ok"

        except KeyError:
            # If we don't have a downstream CID matching in the relay table
            return  # TODO throw an error

    def forward_upstream(self, message,colour):
        up_cid, up_ip, sess_key = self.relay["DownCID": message["CID"], ("UpCID", "UpIP", "SessKey")]
        self.cprint([message["CID"], "upstream", up_ip], "forward",colour)
        new_message = {
            "CID": up_cid,
            # Decrypt the payload (peel one layer of the onion)
            "payload": aes_decrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post("http://" + up_ip, json=new_message)
        return "ok"

    def forward_downstream(self, message,colour):
        down_cid, down_ip, sess_key = self.relay["UpCID": message["CID"], ("DownCID", "DownIP", "SessKey")]

        self.cprint([message["CID"], "downstream", down_ip], "forward",colour)

        new_message = {
            "CID": down_cid,
            # Encrypt the payload (add a layer to the onion)
            "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post("http://" + down_ip, json=new_message)
        return "ok"

    def create_tunnel(self, message,colour):
        if "aes_key" not in message:
            return  # TODO throw an error

        # Decrypt the AES key
        sess_key = rsa_decrypt(bytes.fromhex(message["aes_key"]), self.private_key)
        sess_key = sess_key[-aes_common.key_size:]  # Discard the right padding created by RSA

        # Decrypt the payload with the AES key
        # It should be a JSON string once decoded
        payload = aes_decrypt(bytes.fromhex(message["payload"]), sess_key)
        payload = bytes_to_json(payload)

        if "relay" not in payload or "to" not in payload:
            # All these fields should be present
            return  # TODO throw an error

        # Generate a CID for the upstream link
        up_cid = generate_bytes(cid_size).hex()

        self.cprint([message["CID"]], "unknownCID",colour)
        # Add a line to the relay table
        self.relay[:, ("DownIP", "DownCID", "SessKey", "UpIP", "UpCID")] = \
            (request.remote_addr + ":5000", message["CID"], sess_key, payload["to"], up_cid)

        # Forward the payload to the next node upstream
        new_message = {
            "CID": up_cid,
            # Copy verbatim the encrypted key and payload for the next node (not our business)
            "payload": payload["relay"]
        }
        if "aes_key" in payload:
            new_message["aes_key"] = payload["aes_key"]

        self.cprint([up_cid,payload["to"]], "addToRelay",colour)
        requests.post("http://" + payload["to"], json=new_message)
        return "ok"

    def make_bridge(self, fsid, bridge_cid, bridge_ip,colour):
        self.cprint([bridge_ip, bridge_cid, "outgoing", fsid], "make_bridge",colour)
        self.up_file_transfer[fsid] = (bridge_cid, bridge_ip)

    def receive_bridge(self, bridge_cid, origin_cid,colour):
        down_cid, down_ip = self.relay["UpCID": origin_cid, ("DownCID", "DownIP")]

        self.cprint([down_ip, down_cid], "receive_bridge",colour)
        self.down_file_transfer[bridge_cid] = (down_cid)

    def cprint(self, args, id, colour):
        print(Back.BLACK + colour  + self.statements[id].format(*args), file=sys.stdout)


parser = argparse.ArgumentParser(description='TORrent node')
# We need the IP of the node so that it can find its own private RSA
# key in the network info files.
parser.add_argument('ip', type=str, help='ip address of the node')
args = parser.parse_args()
colorama.init(autoreset=True)
node = Node(__name__, args.ip)
node.run()
