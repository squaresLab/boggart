from flask import Flask


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, world.'


def launch(port: int = 6000) -> None:
    assert 0 <= port <= 49151
    app.run(host='0.0.0.0', port=port)


def main() -> None:
    launch()
