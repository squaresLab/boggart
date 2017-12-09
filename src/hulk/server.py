import flask
import os
from flask import Flask

app = Flask(__name__)

def json_error(msg):
    jsn = {'error': {'msg': msg}}
    return flask.jsonify(jsn)


@app.route('/')
def hello_world():
    return 'Hello, world.'


@app.route('/mutations', methods=['GET'])
def mutations():
    args = flask.request.get_json()

    # determine the file whose mutations the user wishes to obtain
    if 'filepath' not in args:
        return json_error("No 'filepath' argument provided.")
    if not os.path.isfile(args['filepath']):
        return json_error('No file located at given filepath.')
    filepath = args['filepath']

    mutations = []

    return flask.jsonify(mutations)


def launch(port: int = 6000) -> None:
    assert 0 <= port <= 49151
    app.run(port=port)


def main() -> None:
    launch()
