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


class Node(Flask):

    def __init__(self, name, ip):
        super().__init__(name)
        self.add_url_rule("/", "main_handler", self.main_handler, methods=["POST"])
        self.add_url_rule("/control_handler/", "control_handler", self.control_handler, methods=["POST"])
        self.private_key = private_keys[ip]
        self.relay = MIDict([], ["DownIP", "DownCID", "SessKey", "UpIP", "UpCID"])
        self.up_file_transfer = MIDict([], ["FSID", "BridgeCID", "BridgeIP"])
        self.down_file_transfer = MIDict([], ["BridgeCID", "DownCID"])

    def run(self):
        super().run(host='0.0.0.0')

    def main_handler(self):
        message = request.get_json()
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

    def control_handler(self):
        """Tracker control messages will arrive here."""
        # Read message, update table accordingly
        message = request.get_json()
        if request.remote_addr == tracker:
            if "type" in message and message["type"] == "make_bridge":
                self.make_bridge(message["FSID"], message["bridge_CID"], message["to"])
            elif "type" in message and message["type"] == "receive_bridge":
                self.receive_bridge(message["bridge_CID"], message["CID"])

    def transmit_to_bridge(self, message):
        if message["FSID"] not in self.up_file_transfer.indices["FSID"]:
            # We don't have file sharing data about this FSID
            return  # TODO Throw an error

        bridge_ip, bridge_cid = self.up_file_transfer["FSID": message["FSID"], ("BridgeIP", "BridgeCID")]
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

    def receive_from_bridge(self, message):
        down_cid = self.down_file_transfer["BridgeCID": message["CID"], "DownCID"]
        try:
            down_ip, sess_key = self.relay["DownCID": down_cid, "DownIP"]
            new_message = {
                "CID": down_cid,
                # Encrypt the message when sending downstream, we received it as encoded plaintext
                "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
            }
            requests.post("http://" + down_ip, data=new_message)

        except KeyError:
            # If we don't have a downstream CID matching in the relay table
            return  # TODO throw an error

    def forward_upstream(self, message):
        up_cid, up_ip, sess_key = self.relay["DownCID": message["CID"], ("UpCID", "UpIP", "SessKey")]
        new_message = {
            "CID": up_cid,
            # Decrypt the payload (peel one layer of the onion)
            "payload": aes_decrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post("http://" + up_ip, data=new_message)

    def forward_downstream(self, message):
        down_cid, down_ip, sess_key = self.relay["UpCID": message["CID"], ("DownCID", "DownIP", "SessKey")]

        new_message = {
            "CID": down_cid,
            # Encrypt the payload (add a layer to the onion)
            "payload": aes_encrypt(bytes.fromhex(message["payload"]), sess_key).hex()
        }
        requests.post("http://" + down_ip, data=new_message)

    def create_tunnel(self, message):
        if "aes_key" not in message:
            return  # TODO throw an error

        # Decrypt the AES key
        sess_key = rsa_decrypt(bytes.from_hex(message["aes_key"]), self.private_key)
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
        requests.post("http://" + message["to"], data=new_message)

    def make_bridge(self, fsid, bridge_cid, bridge_ip):
        self.up_file_transfer[fsid] = (bridge_cid, bridge_ip)

    def receive_bridge(self, bridge_cid, origin_cid):
        down_cid = self.relay["UpCID": origin_cid, "DownCID"]
        self.down_file_transfer[bridge_cid] = (down_cid)


parser = argparse.ArgumentParser(description='TORrent node')
# We need the IP of the node so that it can find its own private RSA key in
# common/network_info.py
parser.add_argument('ip', type=str, help='ip address of the node')
args = parser.parse_args()
node = Node(__name__, args.ip)
node.run()
