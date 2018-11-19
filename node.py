from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Node"


app.run()


def decrypt():
    """
    Decrypt a layer
    """
    pass
