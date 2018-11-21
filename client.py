import os
import requests
import json
import argparse
from flask import Flask, render_template

from common.network_info import *

parser = argparse.ArgumentParser(description='TORrent client')
parser.add_argument('lof', type=open, help='list of files')

args = parser.parse_args()



def file_list():
    """Parses the JSON document containing the list of files for this
    client

    """
    return json.loads(args.lof.read())


def select_nodes(node_pool):
    """Selects 3 public nodes from the available pool

    """
    pass


def conn():
    """Connect to the torrent network, uploading the list of files this
    client has

    """
    pass


def request_file(file_name):
    """Asks for the file to the tracker

    """
    pass


def client_loop():
    """This function makes the client interactive and puts the terminal in
    a read-eval loop where the input + newline is considered the file
    this client is requesting to the tracker/torrent network




    """
    # read eval loop from stdin
    # send request
    pass



fl = file_list()
sesskeys = []

app = Flask(__name__, template_folder=os.path.abspath('client/templates'))

@app.route("/", methods=['GET'])
def index():
    # Serve HTML page with input to request file
    return render_template("index.html")

@app.route("/", methods=['POST'])
def main_handler():
    """Client will receive comms from the tracker and files from other
    peers on this handler

    """
    # Unencrypt request with keys available, max 3 times !
    pass

@app.route("/request", methods=['POST'])
def request():
    # Get filename wanted
    # Send request to trackere
    print(request)
    return "File requested"


app.run()
