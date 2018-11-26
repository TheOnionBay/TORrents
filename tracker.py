from flask import Flask
from flask import jsonify
app = Flask(__name__)

files = ["titanic", "Harry Potter", "Resident Evil", "MatLab"]
@app.route("/", methods=['POST'])
def index():
    # Process list of files a client has
    return jsonify(files)

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


app.run(host='0.0.0.0')
