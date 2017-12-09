import flask
import os
import hulk.operators as ops
from hulk.exceptions import *
from hulk.base import Language, Operator
from flask import Flask

app = Flask(__name__)

# TODO: return different status code
def json_error(msg):
    jsn = {'error': {'msg': msg}}
    return flask.jsonify(jsn)

# TODO: add GET /operator/:name

@app.route('/operators', methods=['GET'])
def list_operators():
    """
    Produces a list of all operators that are registered Hulk that satisfy a
    set of optionally provided parameters.

    Params:
        language: If supplied, restricts the set of operators to those that
            are compatible with a certain language, given by its name.
    """
    args = flask.request.get_json()

    # get a list of all registered operators
    op_list: List[Operator] = list(ops.registered())

    # perform optional language filtering
    if 'language' in args:
        try:
            language = Language.with_name(args['language'])
        except LanguageNotFound:
            return json_error("Specified language is not currently recognised by Hulk.")

        op_list = [op for op in op_list if op.supports_language(language)]

    # serialize to JSON
    op_list = [op.to_dict() for op in op_list]

    return flask.jsonify(op_list)


@app.route('/mutations', methods=['GET'])
def mutations():
    """
    Determines the set of possible single-order mutations that can be applied
    to a given file.

    Params:
        filepath: The file that should be analyzed.
        language: An optional parameter that can be used to explicitly state
            the language used by the given file. If this parameter is not
            supplied, Hulk will attempt to automatically detect the language
            used by a given file based on its file ending.
    """
    args = flask.request.get_json()

    # determine the file whose mutations the user wishes to obtain
    if 'filepath' not in args:
        return json_error("No 'filepath' argument provided.")
    if not os.path.isfile(args['filepath']):
        return json_error('No file located at given filepath.')
    filepath = args['filepath']

    # if a language is specified, use it
    if 'language' in args:
        language = args['language']
        if not Language.is_supported(language):
            return json_error('The specified language is not supported.')

    # if not, attempt to automatically determine which language should be used
    # based on the file ending of the specified file.
    else:
        language = Language.autodetect(filepath)
        if not language:
            return json_error("Failed to auto-detect language for specified file: '{}'. Try manually specifying the language of the file using 'language'.".format(filepath))


    # determine the set of operators that should be used
    mutations = []

    return flask.jsonify(mutations)


def launch(port: int = 6000) -> None:
    assert 0 <= port <= 49151
    app.run(port=port)


def main() -> None:
    launch()
