from flask import Flask


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, world.'


@app.route('/mutations', methods=['GET'])
def mutations():
    return "Here's a list of mutations..."


def launch(port: int = 6000) -> None:
    assert 0 <= port <= 49151
    app.run(port=port)


def main() -> None:
    launch()
