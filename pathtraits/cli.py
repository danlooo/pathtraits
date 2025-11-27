import click
import inotify.adapters
import os
import logging
from pathtraits.logic import *
from pathtraits.traitsdb import *

logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command(help="Update database once, searches for all directories recursively.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option("-v", "--verbose", "verbose", flag_value=True, default=False)
@click.option(
    "--include-files",
    flag_value=True,
    default=False,
    help="Also search for YAML sidecar files",
)
def batch(path, verbose, include_files):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    db = TraitsDB(path)
    for dirpath, dirnames, filenames in os.walk(path):
        pair = PathPair.find(dirpath)
        if pair:
            db.add_pathpair(pair)
        if include_files:
            yml_files = filter(
                lambda x: x.endswith("yml") or x.endswith("yaml"), filenames
            )
            for file in yml_files:
                file = os.path.join(dirpath, file)
                pair = PathPair.find(file)
                if pair:
                    db.add_pathpair(pair)


@main.command(help="Update database continiously, watches for new or changed files.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option("-v", "--verbose", "verbose", flag_value=True, default=False)
def watch(path, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    print("starting...")
    i = inotify.adapters.InotifyTree(path)
    db = TraitsDB(path)
    print("ready")

    for event in i.event_gen(yield_nones=False):
        (_, type_names, dir_path, filename) = event

        if not type_names.__contains__("IN_CLOSE_WRITE"):
            continue

        path = os.path.join(dir_path, filename)
        pair = PathPair.find(path)
        if pair:
            db.add_pathpair(pair)


@main.command(help="Get traits of a given path")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option("-v", "--verbose", "verbose", flag_value=True, default=False)
def get(path, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    abs_path = os.path.abspath(path)
    leaf_dir = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path
    dirs = leaf_dir.split("/")
    for i in reversed(range(0, len(dirs))):
        if i == 0:
            db_dir = "/"
        else:
            db_dir = "/".join(dirs[0 : i + 1])

        db_path = db_dir + "/.pathtraits.db"
        if not os.path.exists(db_path):
            continue

        # TODO: recursive inheritance of pathtraits
        db = TraitsDB(db_dir)
        data = db.get("data", path=abs_path)
        print(yaml.safe_dump(data))
        return

    KeyError(f"No pathtraits database found in {abs_path} and its parents.")


if __name__ == "__main__":
    main()
