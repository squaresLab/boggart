from typing import Iterator, List
import logging
import os
import json

import bugzoo
import boggart

R1 = '=' * 80
R2 = '-' * 80

BLACKLIST_FILES = [
    'src/yujin_ocs/yocs_cmd_vel_mux/src/cmd_vel_subscribers.cpp'
]


def mutations_in_file(fn: str) -> Iterator[boggart.Mutation]:
    pass


def compute_file_stats(files: List[str]) -> None:
    # find all packages
    pkgs = set(fn.split('/')[1] for fn in files)

    print("{0}\nFile Statistics\n{0}".format(R1))
    print("# mutable files: {}".format(len(files)))
    print("# mutable packages: {}".format(len(pkgs)))
    print(R2)


def compute_line_stats(lines: bugzoo.core.FileLineSet) -> None:
    print("\n{0}\nLine Statistics\n{0}".format(R1))
    print("# mutable lines: {}".format(len(lines)))
    print(R2)


def compute_mutant_stats(boggart_client: boggart.Client,
                         bug: bugzoo.Bug,
                         lines: bugzoo.core.FileLineSet
                         ) -> None:
    op_names = [
        'flip-arithmetic-operator',
        'flip-boolean-operator',
        'delete-conditional-control-flow'
    ]
    ops = [boggart_client.operators[n] for n in op_names]
    mutations = []
    files = lines.files  # type: List[str]
    files = [
        'src/yujin_ocs/yocs_cmd_vel_mux/src/cmd_vel_mux_nodelet.cpp'
    ]
    for fn in files:
        print("- finding mutations in file: {}".format(fn))
        mutations += boggart_client.mutations(bug, fn, operators=ops)

    # write to file
    with open('mutations.json', 'w') as f:
        json.dump([m.to_dict() for m in mutations], f, indent=True)

    print("found {} mutations".format(len(mutations)))


def main():
    log_formatter = \
        logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S')
    # log_to_stdout = logging.StreamHandler()
    # log_to_stdout.setFormatter(log_formatter)
    # log_main = logging.getLogger('boggart')  # type: logging.Logger
    # log_main.setLevel(logging.ERROR)
    # log_main.addHandler(log_to_stdout)

    with boggart.server.ephemeral_stack(verbose=False) as client_boggart:
        client_bugzoo = bugzoo.Client() # type: bugzoo.Client

        # fetch the bug
        bug = client_bugzoo.bugs['mars:base']
        coverage = client_bugzoo.bugs.coverage(bug)
        files = coverage.lines.files
        files = [fn for fn in files if fn.endswith('.cpp')]
        files = [fn for fn in files if not fn.startswith('src/stage_ros')]
        files = [fn for fn in files if not fn.startswith('src/ros')]
        files = [fn for fn in files if not fn in BLACKLIST_FILES]

        lines = coverage.restricted_to_files(files).lines

        compute_file_stats(files)
        compute_line_stats(lines)
        compute_mutant_stats(client_boggart, bug, lines)


if __name__ == '__main__':
    main()
