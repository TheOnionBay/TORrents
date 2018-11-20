from flask import Flask
# import all crypto

app = Flask(__name__)

# Node Attributes : InIP,OutIP, InCID, OutCID, SessionKey

def decrypt():
    """
    Decrypt a layer
    """
    pass

@app.route("/")
def index():
    return "Node"

@app.route("/control", methods=['POST'])
def control():
    """Tracker control messages will arrive here in plaintext, no need to
    decrypt

    """
    # Read message, update table accordingly
    pass


app.run()
