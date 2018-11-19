import requests
from flask import Flask


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
