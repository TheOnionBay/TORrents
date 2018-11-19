from flask import Flask

app = Flask(__name__)

# Node Attributes : InIP,OutIP, InCID, OutCID, SessionKey


@app.route("/")
def index():
    return "Node"


app.run()


def decrypt():
    """
    Decrypt a layer
    """
    pass
