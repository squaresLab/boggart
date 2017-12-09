import flask
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
    try:
        args = flask.request.get_json()

        if 'filepath' not in args:
            return json_error("No 'filepath' argument provided.")
        filepath = args['filepath']

        mutations = []

        return flask.jsonify(mutations)

    except JSONException as e:
        return e.jsonify()


def launch(port: int = 6000) -> None:
    assert 0 <= port <= 49151
    app.run(port=port)


def main() -> None:
    launch()
