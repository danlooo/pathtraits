import click
import inotify.adapters
import re
import os
import logging
from pathtraits.logic import *
from pathtraits.traitsdb import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@click.group()
def main():
    pass


@main.command()
@click.argument("path", required=True)
def start(path):
    print("starting...")
    i = inotify.adapters.InotifyTree(path)
    db = TraitsDB(path)
    print("ready")

    yaml_re = re.compile(r"\.(yaml|yml)$")
    for event in i.event_gen(yield_nones=False):
        (_, type_names, dir_path, filename) = event

        if not type_names.__contains__("IN_CLOSE_WRITE"):
            continue

        path = os.path.join(dir_path, filename)
        pair = PathPair.find(path)
        if pair:
            db.add_pathpair(pair)


if __name__ == "__main__":
    main()
