from flask import Flask
from flask import jsonify
app = Flask(__name__)

files = ["titanic", "Harry Potter", "Resident Evil", "MatLab"]
@app.route("/")
def index():
    # Process list of files a client has
    return jsonify(files)


app.run()
