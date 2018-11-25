import os
from flask import Flask, render_template
from flask import jsonify
from common.network_info import *

app = Flask(__name__, template_folder=os.path.abspath('tracker/templates'))

files = {"movie1": "cid1",
         "movie2": "cid2",
         "movie3": "cid3"}

peers = {"cid1": "IP1",
         "cid2": "IP2"}


def send_filestore(cid):
    """Clients need the list of all files available in the network
    (statement of the project). Therefore this function has to be
    called at some point to share that list of files with the clients.

    """
    # send files to cid.
    pass


@app.route("/", methods=['POST'])
def index2():
    return "is this route necessary ?"

@app.route("/", methods=['GET'])
def index():
    # Process list of files a client has
    return render_template("index.html",
                           data={"file_list": list(files.keys()),
                                 "peers": peers})

@app.route("/announce", methods=['POST'])
def announce():
    """Gets list of files from some client and updates table accordingly.

    """
    pass

@app.route("/request", methods=['POST'])
def request():
    """Gets the name of the file wanted by some peer and check
    availability

    """
    pass


app.run()
