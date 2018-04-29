import pytest
import os
import signal
import subprocess
import time
from contextlib import contextmanager

import bugzoo.client
from boggart.server import Installation


@contextmanager
def bugzoo_test_server(port: int = 6060) -> None:
    try:
        url = "http://127.0.0.1:{}".format(port)
        cmd = ["bugzood", "--port", str(port)]
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   preexec_fn=os.setsid)
        yield bugzoo.client.Client(url)
    finally:
        os.killpg(process.pid, signal.SIGTERM)


def read_file_contents():
    with bugzoo_test_server() as bugzoo:
        snapshot_test = bugzoo.bugs["tse2012:gcd"]
        # bugzoo.bugs.build(snapshot_test)

        # the file that we want to fetch
        fn = "gcd.c"

        boggart = Installation.load(bugzoo)
        contents = boggart.read_file_contents(snapshot_test, fn)

        print(contents)


if __name__ == "__main__":
    read_file_contents()
