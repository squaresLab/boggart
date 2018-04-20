from typing import Optional
from functools import wraps
import argparse
import os

import bugzoo
import flask
from flask_api import FlaskAPI

from .exceptions import *
from .base import Language, Operator
from .hulk import Hulk

app = FlaskAPI(__name__)

# TODO: tidy this up
installation = None # type: Optional[Hulk]


def throws_errors(func):
    """
    Wraps a function responsible for implementing an API endpoint such that
    any server errors that are thrown are automatically transformed into
    appropriate HTTP responses.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientServerError as err:
            return err.to_response()
    return wrapper


@app.route('/languages/<name>', methods=['GET'])
@throws_errors
def describe_language(name: str):
    """
    Provides a description of a given language, specified by its name.

    Raises:
        LanguageNotFound: if no language is registered with this server
            under the given name.
    """
    try:
        language = installation.languages[name]
        return language.to_dict()
    except KeyError:
        raise LanguageNotFound(name)


@app.route('/languages', methods=['GET'])
def list_languages():
    """
    Produces a list of all languages that are supported by this server.
    """
    return [lang.to_dict() for lang in installation.languages]


@app.route('/operators/<name>', methods=['GET'])
@throws_errors
def describe_operator(name: str):
    """
    Describes a named operator.
    """
    try:
        return installation.operators[name].to_dict()
    except KeyError:
        raise OperatorNotFound(name)


@app.route('/operators', methods=['GET'])
@throws_errors
def list_operators():
    """
    Produces a list of all operators that are registered Hulk that satisfy a
    set of optionally provided parameters.

    Params:
        language: If supplied, restricts the set of operators to those that
            are compatible with a certain language, given by its name.
    """
    # TODO use URL params
    args = flask.request.get_json()
    if args is None:
        args = {}

    # get a list of all registered operators
    op_list: List[Operator] = list(installation.operators)

    # perform optional language filtering
    if 'language' in args:
        try:
            language = installation.languages[args['language']]
        except KeyError:
            raise LanguageNotFound(args['language'])

        op_list = [op for op in op_list if op.supports_language(language)]

    # serialize to JSON
    op_list = [op.to_dict() for op in op_list]
    return op_list


@app.route('/files/:snapshot/:filepath', methods=['GET'])
@throws_errors
def read_file(name_snapshot: str, fn: str):
    """
    Reads the contents of a specified file in a given snapshot.
    """
    cache_key = (name_snapshot, fn)
    if cache_key in hulk._cache_file_contents:
        contents = hulk._cache_file_contents[cache_key]
        # TODO ensure correct response encoding
        return contents, 400

    try:
        snapshot = hulk.bugzoo.bugs[name_snapshot]
    except KeyError:
        raise SnapshotNotFound(name_snapshot)

    container = hulk.bugzoo.containers.provision(snapshot)
    try:
        contents = hulk.bugzoo.files.read(container, fn)
        hulk._cache_file_contents[cache_key] = contents
        # TODO ensure correct response encoding
        return contents, 400
    except KeyError:
        raise FileNotFound(fn)
    finally:
        del hulk.bugzoo.containers[container.uid]


@app.route('/mutations/:filepath', methods=['GET'])
@throws_errors
def mutations(fn: str):
    """
    Determines the set of possible single-order mutations that can be applied
    to a given file.

    Params:
        fn: The file that should be analyzed.
        language: An optional parameter that can be used to explicitly state
            the language used by the given file. If this parameter is not
            supplied, Hulk will attempt to automatically detect the language
            used by a given file based on its file ending.
    """
    args = flask.request.args

    # determine the file whose mutations the user wishes to obtain
    if not os.path.isfile(fn):
        return json_error('No file located at given filepath.')

    # if a language is specified, use it
    if 'language' in args:
        language = args['language']
        if language not in installation.languages:
            return json_error('The specified language is not supported.')

    # if not, attempt to automatically determine which language should be used
    # based on the file ending of the specified file.
    else:
        # TODO add error
        language = installation.detect_language(fn)
        if not language:
            return json_error("Failed to auto-detect language for specified file: '{}'. Try manually specifying the language of the file using 'language'.".format(fn))


    # determine the set of operators that should be used
    mutations = []

    return mutations


def launch(port: int = 8000,
           url_bugzoo: str = 'http://127.0.0.1:6060'
           ) -> None:
    global installation
    assert 0 <= port <= 49151
    client_bugzoo = bugzoo.client.Client(url_bugzoo)
    installation = Hulk.load(client_bugzoo)
    app.run(port=port, debug=True)


def main() -> None:
    desc = 'Hulk'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port',
                        type=int,
                        default=8000,
                        help='the port that should be used by this server.')
    parser.add_argument('--bugzoo',
                        type=str,
                        default='http://127.0.0.1:6060',
                        help='the URL of the BugZoo server.')
    args = parser.parse_args()
    launch(port=args.port,
           url_bugzoo=args.bugzoo)
