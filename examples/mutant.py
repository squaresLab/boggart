from contextlib import contextmanager
import os
import signal
import subprocess
import time

import boggart
import bugzoo


@contextmanager
def bugzoo_test_server(port: int = 6060) -> None:
    url = "http://127.0.0.1:{}".format(port)
    cmd = ["bugzood", "--port", str(port)]
    print("launching bugzoo at {} via '{}'".format(url, ' '.join(cmd)))
    try:
        process = subprocess.Popen(cmd,
                                   #stdout=subprocess.DEVNULL,
                                   #stderr=subprocess.DEVNULL,
                                   preexec_fn=os.setsid)
        yield bugzoo.client.Client(url)
    finally:
        os.killpg(process.pid, signal.SIGTERM)


@contextmanager
def boggart_test_server(url_bugzoo: str, port: int = 8000) -> None:
    url = "http://127.0.0.1:{}".format(port)
    cmd = ["boggartd", "--bugzoo", url_bugzoo, "-p", str(port)]
    print("launching boggartd at {} via '{}'".format(url, ' '.join(cmd)))
    try:
        process = subprocess.Popen(cmd,
                                   preexec_fn=os.setsid)
                                   #stdout=subprocess.DEVNULL,
                                   #stderr=subprocess.DEVNULL)
        yield boggart.Client(url)
    finally:
        os.killpg(process.pid, signal.SIGTERM)


@contextmanager
def test_env(port_bugzoo: int = 6060, port_boggart: int = 8000) -> None:
    url_bugzoo = "http://127.0.0.1:{}".format(port_bugzoo)
    with bugzoo_test_server(port_bugzoo) as client_bugzoo:
        with boggart_test_server(url_bugzoo, port_boggart) as client_boggart:
            yield (client_bugzoo, client_boggart)


def generate_mutant():
    with test_env() as (client_bugzoo, client_boggart):
        snapshot = client_bugzoo.bugs["tse2012:gcd"]
        location = boggart.FileLocationRange.from_string("gcd.c@10:3::10:15")
        mutation = boggart.Mutation("NEGATE_IF_CONDITION_CSTYLE", 0, location, {})
        mutations = [mutation]
        mutant = client_boggart.mutate(snapshot, mutations)
        print(mutant)
        print(mutant.uuid)
        print(mutant.to_dict())


if __name__ == '__main__':
    generate_mutant()
