from typing import Optional, List, Dict, Any
from functools import wraps
from uuid import UUID
import argparse
import os

import bugzoo
import flask
import rooibos
from flask_api import FlaskAPI

from .installation import Installation
from ..exceptions import *
from ..core import Language, Operator, Mutation

app = FlaskAPI(__name__)

# TODO: tidy this up
installation = None # type: Optional[Installation]


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


@app.route('/status', methods=['GET'])
@throws_errors
def status():
    """
    Produces a diagnostic summary of the health of the server.
    """
    return '', 204


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
    Produces a list of all operators that are registered with boggart that
    satisfy a set of optionally provided parameters.

    Params:
        language: If supplied, restricts the set of operators to those that
            are compatible with a certain language, given by its name.
    """
    # TODO use URL params
    args = flask.request.get_json()
    if args is None:
        args = {}

    # get a list of all registered operators
    op_list = list(installation.operators) # type: List[Operator]

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


@app.route('/mutants', methods=['GET', 'POST'])
@throws_errors
def interact_with_mutants():
    if flask.request.method == 'GET':
        list_uuid = [m.uuid for m in installation.mutants]
        return flask.jsonify(list_uuid), 200

    if flask.request.method == 'POST':
        description = flask.request.json
        print(description)
        snapshot_name = description['snapshot']
        try:
            snapshot = installation.bugzoo.bugs[snapshot_name]
        except KeyError:
            return SnapshotNotFound(snapshot_name), 404

        mutations = [Mutation.from_dict(m) for m in description['mutations']]
        mutant = installation.mutants.generate(snapshot, mutations)
        jsn_mutant = mutant.to_dict()
        return flask.jsonify(jsn_mutant), 200


@app.route('/mutants/<uuid_str>', methods=['GET'])
@throws_errors
def interact_with_mutant(uuid_hex: str):
    uuid = UUID(hex=uuid_hex)

    if flask.request.method == 'GET':
        mutant = installation.mutants[uuid]
        return flask.jsonify(mutant.to_dict()), 200


@app.route('/mutations/<name_snapshot>/<filepath>', methods=['GET'])
@throws_errors
def mutations(name_snapshot: str, filepath: str):
    """
    Determines the set of possible single-order mutations that can be applied
    to a given file belonging to a specified BugZoo snapshot.

    Path Parameters:
        name_snapshot: The name of the BugZoo snapshot that should be mutated.
        filepath: The file that should be analyzed.

    URL-encoded Parameters:
        language: An optional parameter that can be used to explicitly state
            the language used by the given file. If this parameter is not
            supplied, boggart will attempt to automatically detect the language
            used by a given file based on its file ending.
        operators: An optional semi-colon delimited parameter that can be used
            to specify which mutation operators should be used. If left
            unspecified, all available mutation operators for the language used
            by the given file will be used.

    Raises:
        SnapshotNotFound: if no snapshot can be found with the given name.
        FileNotFound: if the given file is not found inside the snapshot.
        LanguageNotFound: if the given language is not recognized by the
            server.
        LanguageNotDetected: if the language used by the given file cannot be
            automatically detected.
    """
    args = flask.request.args

    # fetch the given snapshot
    try:
        snapshot = installation.bugzoo.bugs[name_snapshot]
    except KeyError:
        raise SnapshotNotFound(name_snapshot)

    # determine the language used by the file
    if 'language' in args:
        try:
            language = installation.languages[args['language']]
        except KeyError:
            raise LanguageNotFound(args['language'])
    else:
        language = None

    # determine the set of operators that should be used
    if 'operators' in args:
        operators = []
        operator_names = args['operators'].split(';')
        for name in operator_names:
            try:
                op = installation.operators[name]
                operators.append(op)
            except KeyError:
                raise OperatorNotFound(name)
    else:
        operators = None

    # TODO implement line restriction

    mutations = installation.mutations(snapshot,
                                       filepath,
                                       language=language,
                                       operators=operators)
    jsn = [m.to_dict() for m in mutations]
    return jsn


def launch(port: int = 8000,
           url_bugzoo: str = 'http://127.0.0.1:6060',
           url_rooibos: str = 'http://host.docker.internal:8888',
           host: str = '0.0.0.0',
           debug: bool = False
           ) -> None:
    global installation
    assert 0 <= port <= 49151
    client_bugzoo = bugzoo.client.Client(url_bugzoo)
    client_rooibos = rooibos.Client(url_rooibos, timeout_connection = 60)
    installation = Installation.load(client_bugzoo, client_rooibos)
    app.run(port=port, host=host, debug=debug)


def main() -> None:
    desc = 'boggart'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port',
                        type=int,
                        default=8000,
                        help='the port that should be used by this server.')
    parser.add_argument('--rooibos',
                        type=str,
                        default='http://host.docker.internal:8888',
                        help='the URL of the Rooibos server.')
    parser.add_argument('--bugzoo',
                        type=str,
                        default='http://127.0.0.1:6060',
                        help='the URL of the BugZoo server.')
    parser.add_argument('--host',
                        type=str,
                        default='0.0.0.0',
                        help='the IP address of the host.')
    parser.add_argument('--debug',
                        action='store_true',
                        help='enables debugging mode.')
    args = parser.parse_args()
    launch(port=args.port,
           url_bugzoo=args.bugzoo,
           url_rooibos=args.rooibos,
           host=args.host,
           debug=args.debug)
