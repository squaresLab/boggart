from typing import Tuple, Iterator
from contextlib import contextmanager
from pprint import pprint
import os
import signal
import subprocess
import time

import boggart
import bugzoo
import rooibos


@contextmanager
def test_environment(port_bugzoo: int = 6060,
                     port_rooibos: int = 8888,
                     port_boggart: int = 8000,
                     verbose: bool = True
                     ) -> Iterator[Tuple[boggart.Client, bugzoo.Client]]:
    url_bugzoo = "http://127.0.0.1:{}".format(port_bugzoo)
    with boggart.server.ephemeral_stack(port_boggart=port_boggart,
                                        port_rooibos=port_rooibos,
                                        port_bugzoo=port_bugzoo,
                                        verbose=verbose) as client_boggart:
        client_bugzoo = bugzoo.Client(url_bugzoo)
        print(client_boggart)
        print(client_bugzoo)
        yield client_boggart, client_bugzoo


def generate_mutant():
    with test_environment() as (client_boggart, client_bugzoo):
        snapshot = client_bugzoo.bugs["tse2012:gcd"]
        location = boggart.FileLocationRange.from_string("gcd.c@10:3::10:15")
        mutation = boggart.Mutation("NEGATE_IF_CONDITION_CSTYLE", 0, location, {})
        mutations = [mutation]
        mutant = client_boggart.mutate(snapshot, mutations)
        print(mutant)
        print(mutant.uuid)
        print(mutant.to_dict())


def generate_mutations():
    with test_environment() as (client_boggart, client_bugzoo):
        snapshot = client_bugzoo.bugs["tse2012:gcd"]
        filepath = "gcd.c"
        for mutation in client_boggart.mutations(snapshot, filepath):
            pprint(mutation.to_dict())


if __name__ == '__main__':
    generate_mutations()
