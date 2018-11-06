from flask import Flask
app = Flask(__name__)


@app.route("/")
def index():
    # Process list of files a client has
    return "Hello World!"


app.run()
