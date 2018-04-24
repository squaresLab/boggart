from contextlib import contextmanager
import os
import signal
import subprocess
import time

import hulk
import bugzoo


@contextmanager
def bugzoo_test_server(port: int = 6060) -> None:
    url = "http://127.0.0.1:{}".format(port)
    cmd = ["bugzood"] # "--port", str(port)]
    print("launching bugzoo at {} via '{}'".format(url, ' '.join(cmd)))
    try:
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   preexec_fn=os.setsid)
        # TODO adding waiting to client constructor
        time.sleep(15)
        yield bugzoo.client.Client(url)
    finally:
        os.killpg(process.pid, signal.SIGTERM)


@contextmanager
def hulk_test_server(url_bugzoo: str, port: int = 8000) -> None:
    url = "http://127.0.0.1:{}".format(port)
    cmd = ["hulkd", "--bugzoo", url_bugzoo, "-p", str(port)]
    print("launching hulk at {} via '{}'".format(url, ' '.join(cmd)))
    try:
        process = subprocess.Popen(cmd,
                                   preexec_fn=os.setsid,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        # TODO adding waiting to client constructor
        time.sleep(5)
        yield hulk.Client(url)
    finally:
        os.killpg(process.pid, signal.SIGTERM)


@contextmanager
def test_env(port_bugzoo: int = 6060, port_hulk: int = 8000) -> None:
    url_bugzoo = "http://127.0.0.1:{}".format(port_bugzoo)
    with bugzoo_test_server(port_bugzoo) as client_bugzoo:
        with hulk_test_server(url_bugzoo, port_hulk) as client_hulk:
            yield (client_bugzoo, client_hulk)


def generate_mutant():
    with test_env() as (client_bugzoo, client_hulk):
        print(list(client_hulk.operators))


if __name__ == '__main__':
    generate_mutant()
