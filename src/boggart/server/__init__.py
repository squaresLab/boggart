from typing import Optional, List, Dict, Any, Iterator
from functools import wraps
from contextlib import contextmanager
from uuid import UUID
import argparse
import os
import signal
import subprocess
import threading
import logging
import logging.handlers
import sys
import time

import bugzoo
import bugzoo.server
import flask
import rooibos
import flask_api
import requests
from flask_api import FlaskAPI
from bugzoo.util import report_system_resources, report_resource_limits

from .installation import Installation
from ..exceptions import *
from ..core import Language, Operator, Mutation
from ..client import Client
from ..version import __version__

app = FlaskAPI(__name__)
app.logger.disabled = True
logging.getLogger('werkzeug').disabled = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_to_file = None  # type: Optional[logging.handlers.WatchedFileHandler]

# TODO: tidy this up
installation = None  # type: Any


@app.errorhandler(Exception)
def unexpected_error_handler(err: Exception):
    """
    Captures any unexpected errors.
    """
    logger.error("Encountered an unexpected error", err)
    try:
        err_report = UnexpectedServerError.from_exception(err)
        return err_report.to_response()
    except Exception:
        return '', 500


@contextmanager
def ephemeral(*,
              url_bugzoo: str = 'http://127.0.0.1:6060',
              url_rooibos: str = 'http://127.0.0.1:8888',
              port: int = 8000,
              verbose: bool = False
              ) -> Iterator[Client]:
    """
    Launches an ephemeral server instance that will be immediately
    close when no longer in context.

    Parameters:
        port: the port that the server should run on.
        verbose: if set to True, the server will print its output to the
            stdout, otherwise it will remain silent.

    Returns:
        a client for communicating with the server.
    """
    url = "http://127.0.0.1:{}".format(port)
    cmd = ["boggartd",
           "-p", str(port),
           "--bugzoo", url_bugzoo,
           "--rooibos", url_rooibos]
    try:
        stdout = None if verbose else subprocess.DEVNULL
        stderr = None if verbose else subprocess.DEVNULL
        proc = subprocess.Popen(cmd,
                                preexec_fn=os.setsid,
                                stdout=stdout,
                                stderr=stderr)
        yield Client(url)
    finally:
        os.killpg(proc.pid, signal.SIGTERM)


@contextmanager
def ephemeral_stack(*,
                    port_boggart: int = 8000,
                    port_rooibos: int = 8888,
                    port_bugzoo: int = 6060,
                    verbose: bool = False
                    ) -> Iterator[Client]:
    """
    Launches an ephemeral server instance along with a complete underlying
    stack (i.e., an ephemeral Rooibos and BugZoo), all of which will be
    immediately destroyed upon leaving the context.

    Parameters:
        port_boggart: the port that the boggart server should run on.
        port_rooibos: the port that the Rooibos server should run on.
        port_bugzoo: the port that the BugZoo server should run on.
        verbose: if set to True, the server will print its output to the
            stdout, otherwise it will remain silent.

    Returns:
        a client for communicating with the boggart server.
    """
    url_rooibos = "http://127.0.0.1:{}".format(port_rooibos)
    url_bugzoo = "http://127.0.0.1:{}".format(port_bugzoo)
    with bugzoo.server.ephemeral(port=port_bugzoo,
                                 verbose=verbose) as client_bz:
        with rooibos.ephemeral_server(port=port_rooibos,
                                      verbose=verbose) as client_rooibos:
            with ephemeral(url_rooibos=url_rooibos,
                           url_bugzoo=url_bugzoo,
                           port=port_boggart,
                           verbose=verbose) as client_boggart:
                yield client_boggart


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
            logger.exception("encountered an error while handling request: %s", err.message)  # noqa: pycodestyle
            return err.to_response()
        except Exception as err:
            logger.exception("encountered unexpected error while handling request: %s", err)  # noqa: pycodestyle
            return UnexpectedServerError.from_exception(err).to_response()
    return wrapper


@app.route('/shutdown', methods=['POST'])
def shutdown():
    installation.mutants.clear()
    if log_to_file:
        log_to_file.flush()

    def self_destruct() -> None:
        wait_time = 3
        for i in range(3, 0, -1):
            logger.info("Closing server in %d seconds...", i)
            time.sleep(1.0)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=self_destruct).run()

    return '', 202


@app.route('/status', methods=['GET'])
@throws_errors
def status():
    """
    Produces a diagnostic summary of the health of the server.
    """
    logger.info("inspecting server health")
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
    logger.info("attempting to find language with name: %s", name)
    try:
        language = installation.languages[name]
        logger.info("found language with name %s: %s", name, language)
        return language.to_dict()
    except KeyError:
        logger.error("failed to find language: %s", name)
        raise LanguageNotFound(name)


@app.route('/languages', methods=['GET'])
def list_languages():
    """
    Produces a list of all languages that are supported by this server.
    """
    logger.info("retrieving list of supported languages")
    return [lang.to_dict() for lang in installation.languages]


@app.route('/operators/<name>', methods=['GET'])
@throws_errors
def describe_operator(name: str):
    """
    Describes a named operator.
    """
    logger.info("attempting to find operator with name: %s", name)
    try:
        operator = installation.operators[name]
        logger.info("found operator with name %s: %s", name, operator)
        return operator.to_dict()
    except KeyError:
        logger.error("failed to find operator: %s", name)
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
    logger.info("requesting list of operators", extra=args)

    # get a list of all registered operators
    op_list = list(installation.operators)  # type: List[Operator]

    # perform optional language filtering
    if 'language' in args:
        try:
            language = installation.languages[args['language']]
        except KeyError:
            raise LanguageNotFound(args['language'])

        op_list = [op for op in op_list if op.supports_language(language)]

    # serialize to JSON
    jsn_op_list = [op.to_dict() for op in op_list]
    logger.info("operators that satisfy given constraints: [%s]",
                ', '.join([op.name for op in op_list]),
                extra={'operators': jsn_op_list})
    return jsn_op_list


@app.route('/diff/mutations/<name_snapshot>', methods=['PUT'])
@throws_errors
def mutations_to_diff(name_snapshot: str):
    """
    Transforms a set of mutations to a given snapshot into a unified diff.
    """
    sources = installation.sources
    logger.info("attempting to transform mutations into unified diff")
    logger.debug("attempting to retrieve snapshot: %s", name_snapshot)
    try:
        snapshot = installation.bugzoo.bugs[name_snapshot]
    except KeyError:
        logger.exception("failed to find snapshot: %s", name_snapshot)
        raise SnapshotNotFound(name_snapshot)

    logger.debug("extracting mutations from payload")
    try:
        mutations = \
            [Mutation.from_dict(m) for m in flask.request.json['mutations']]
    except KeyError:
        logger.exception("failed to transform mutations into unified diff: failed to read mutations from payload.")  # noqa: pycodestyle
        raise BadFormat("expected a JSON-encoded list of mutations")
    logger.debug("extracted mutations from payload")

    diff = sources.mutations_to_diff(snapshot, mutations)
    diff_s = str(diff)
    logger.info("transformed mutations into unified diff.")
    return diff_s, 200


@app.route('/replacements/mutations/<name_snapshot>', methods=['PUT'])
@throws_errors
def mutations_to_replacements(name_snapshot: str):
    """
    Transforms a set of mutations to a given snapshot into a set of
    replacements.
    """
    sources = installation.sources
    logger.info("attempting to transform mutations into a set of replacements")
    try:
        snapshot = installation.bugzoo.bugs[name_snapshot]
    except KeyError:
        logger.exception("failed to find snapshot: %s", name_snapshot)
        raise SnapshotNotFound(name_snapshot)

    logger.debug("extracting mutations from payload")
    try:
        mutations = \
            [Mutation.from_dict(m) for m in flask.request.json['mutations']]
    except KeyError:
        logger.exception("failed to transform mutations into unified diff: failed to read mutations from payload")  # noqa: pycodestyle
        raise BadFormat("expected a JSON-encoded list of mutations")
    logger.debug("extracted mutations from payload")

    fn_to_replacements = sources.mutations_to_replacements(snapshot, mutations)
    replacements = [r for freps in fn_to_replacements.values() for r in freps]
    jsn = [r.to_dict() for r in replacements]
    logger.info("transformed mutations into a set of replacements: %s",
                replacements)
    return flask.jsonify(jsn), 200


@app.route('/mutants', methods=['GET', 'POST'])
@throws_errors
def interact_with_mutants():
    if flask.request.method == 'GET':
        logger.info("request list of mutants")
        list_uuid = [m.uuid for m in installation.mutants]
        logger.info("%d mutants: %s", len(list_uuid), list_uuid,
                    extra={'mutants': list_uuid})
        return flask.jsonify(list_uuid), 200

    if flask.request.method == 'POST':
        description = flask.request.json
        snapshot_name = description['snapshot']
        logger.info("generating mutant of snapshot '%s'",
                    snapshot_name,
                    extra={'payload': description})
        try:
            snapshot = installation.bugzoo.bugs[snapshot_name]
        except KeyError:
            logger.error("failed to generate mutant: snapshot (%s) was not found",  # noqa: pycodestyle
                         snapshot_name,
                         exc_info=True)
            return SnapshotNotFound(snapshot_name), 404

        mutations = [Mutation.from_dict(m) for m in description['mutations']]
        logger.debug("generating mutant of snapshot '%s' using mutations: %s",
                     snapshot_name, mutations)
        mutant = installation.mutants.generate(snapshot, mutations)
        logger.info("generated mutant: %s", mutant)
        jsn_mutant = mutant.to_dict()
        return flask.jsonify(jsn_mutant), 200


@app.route('/mutants', methods=['DELETE'])
@throws_errors
def clear_mutants():
    installation.mutants.clear()
    return '', 204


@app.route('/mutants/<uuid_hex>', methods=['GET'])
@throws_errors
def interact_with_mutant(uuid_hex: str):
    uuid = UUID(hex=uuid_hex)

    if flask.request.method == 'GET':
        logger.info("fetching information about mutant: %s", uuid)
        try:
            mutant = installation.mutants[uuid]
        except Exception:
            logger.exception("failed to find mutant: %s", uuid)
            raise MutantNotFound(uuid_hex)
        return flask.jsonify(mutant.to_dict()), 200


@app.route('/mutants/<uuid_hex>', methods=['DELETE'])
@throws_errors
def delete_mutant(uuid_hex: str):
    uuid = UUID(hex=uuid_hex)
    logger.info("destroying mutant: %s", uuid_hex)
    try:
        mutant = installation.mutants[uuid]
        logger.info("destroyed mutant: %s", uuid_hex)
    except Exception:
        logger.exception("failed to find mutant: %s", uuid_hex)
        raise MutantNotFound(uuid_hex)
    return '', 204


@app.route('/mutations/<name_snapshot>/<path:filepath>', methods=['GET'])
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
    logger.info("attempting to find mutations to file '%s' belonging to snapshot '%s'",  # noqa: pycodestyle
                filepath,
                name_snapshot,
                extra={'arguments': args})

    # fetch the given snapshot
    logger.debug("attempting to retrieve snapshot: %s", name_snapshot)
    try:
        snapshot = installation.bugzoo.bugs[name_snapshot]
    except KeyError:
        logger.exception("failed to find snapshot: %s", name_snapshot)
        raise SnapshotNotFound(name_snapshot)
    logger.debug("retrieved snapshot: %s", name_snapshot)

    # determine the language used by the file
    if 'language' in args:
        logger.info("obtaining language from arguments")
        try:
            language = installation.languages[args['language']]
        except KeyError:
            raise LanguageNotFound(args['language'])
    else:
        logger.info("no language specified -- attempt to autodetect.")
        language = None

    # determine the set of operators that should be used
    if 'operators' in args:
        operators = []
        operator_names = args['operators'].split(';')
        logger.info("finding operators specified by argument: %s",
                    args['operators'],
                    extra={'operators': operator_names})
        for name in operator_names:
            try:
                logger.debug("looking for operator: %s", name)
                op = installation.operators[name]
                logger.debug("found operator with name %s: %s", name, op)
                operators.append(op)
            except KeyError:
                logger.exception("failed to find operator: %s", name)
                raise OperatorNotFound(name)
    else:
        logger.info("using all available operators to generate mutations")
        operators = list(installation.operators)

    # TODO implement line restriction
    lines = None  # type: Optional[List[int]]
    if 'lines' in args:
        lines = [int(l) for l in args['lines'].split(';')]
        logger.debug("restricting mutations to lines: %s", lines)
    try:
        generator_mutations = \
            installation.mutations(snapshot,
                                   filepath,
                                   language=language,
                                   operators=operators,
                                   restrict_to_lines=lines)
        mutations = list(generator_mutations)
    except BoggartException as e:
        logger.exception("failed to find mutations due to error: %s", e.message)  # noqa: pycodestyle
        raise
    except Exception as e:
        logger.exception("failed to find mutations due to unexpected error: %s", e)  # noqa: pycodestyle
        raise

    logger.info("found %d mutations of file '%s' in snapshot '%s' that satisfy the given constraints.",  # noqa: pycodestyle
                len(mutations),
                filepath,
                name_snapshot)

    logger.debug("serialising discovered mutations")
    jsn = [m.to_dict() for m in mutations]
    logger.debug("serialised discovered mutations")
    return jsn


def launch(port: int = 8000,
           url_bugzoo: str = 'http://127.0.0.1:6060',
           url_rooibos: str = 'http://host.docker.internal:8888',
           host: str = '0.0.0.0',
           log_filename: Optional[str] = None,
           log_level: str = 'info'
           ) -> None:
    global installation, log_to_file

    assert 0 <= port <= 49151

    log_formatter = \
        logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s',
                          '%Y-%m-%d %H:%M:%S')

    if not log_filename:
        log_filename = "boggartd.log"
        log_filename = os.path.join(os.getcwd(), log_filename)

    if log_level != 'none':
        log_level_num = ({
            'none': logging.NOTSET,
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'critical': logging.CRITICAL
        })[log_level]  # type: int

        log_to_file = \
            logging.handlers.WatchedFileHandler(log_filename, mode='w')
        log_to_file.setLevel(log_level_num)
        log_to_file.setFormatter(log_formatter)

        log_to_stdout = logging.StreamHandler()
        log_to_stdout.setLevel(max(log_level_num, logging.INFO))
        log_to_stdout.setFormatter(log_formatter)

        log_main = logging.getLogger('boggart')  # type: logging.Logger
        log_main.setLevel(log_level_num)
        log_main.addHandler(log_to_stdout)
        log_main.addHandler(log_to_file)

        log_rooibos = logging.getLogger('rooibos')  # type: logging.Logger
        log_rooibos.setLevel(logging.ERROR)

    logger.info("Boggart version: %s", __version__)
    logger.info("BugZoo version: %s", bugzoo.__version__)
    logger.info("Rooibos version: %s", rooibos.__version__)
    logger.info("requests version: %s", requests.__version__)
    logger.info("Flask version: %s", flask.__version__)
    logger.info("Flask-API version: %s", flask_api.__version__)

    logger.info("attempting to connect to BugZoo server: %s", url_bugzoo)
    client_bugzoo = bugzoo.client.Client(url_bugzoo)
    logger.info("connected to BugZoo server")
    logger.info("attempting to connect to Rooibos server: %s",
                url_rooibos)
    client_rooibos = rooibos.Client(url_rooibos, timeout_connection=60)
    logger.info("connected to Rooibos server")
    try:
        installation = Installation.load(client_bugzoo, client_rooibos)
        report_system_resources(logger)
        report_resource_limits(logger)
        logger.info("launching HTTP server at %s:%d", host, port)
        app.run(port=port, host=host, debug=False)
    finally:
        installation.mutants.clear()


def main() -> None:
    desc = 'boggart'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port',
                        type=int,
                        default=8000,
                        help='the port that should be used by this server.')
    parser.add_argument('--log-level',
                        type=str,
                        choices=['none',
                                 'info',
                                 'error',
                                 'warning',
                                 'debug',
                                 'critical'],
                        default='info')
    parser.add_argument('--log-file',
                        type=str,
                        help='the path to the file where logs should be written.')  # noqa: pycodestyle
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
    args = parser.parse_args()

    launch(port=args.port,
           url_bugzoo=args.bugzoo,
           url_rooibos=args.rooibos,
           host=args.host,
           log_filename=args.log_file,
           log_level=args.log_level)
