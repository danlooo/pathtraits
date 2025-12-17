import click
import inotify.adapters
import os
import sys
import logging
from pathtraits.pathpair import *
from pathtraits.traitsdb import *
from collections.abc import Callable

logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


def scan_meta_yml(path, yml_paths=[]):
    yml_extensions = [
        "meta.yml",
        "meta.yaml",
        ".meta.yml",
        ".meta.yaml",
        ".yml",
        ".yaml",
    ]
    # faster than os.walk
    with os.scandir(path) as ents:
        for e in ents:
            if e.is_dir():
                scan_meta_yml(e.path, yml_paths)
            else:
                for yml_extension in yml_extensions:
                    if e.path.endswith(yml_extension):
                        object_path = e.path.replace(f".{yml_extension}", "")
                        pair = PathPair(object_path, e.path)
                        yml_paths.append(pair)
                        break
    return yml_paths


@main.command(help="Update database once, searches for all directories recursively.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
@click.option(
    "--include-files",
    flag_value=True,
    default=False,
    help="Also search for YAML sidecar files",
)
def batch(path, db_path, verbose, include_files):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if db_path is None:
        db_path = path + "/.pathtraits.db"
    db = TraitsDB(db_path)
    pathpairs = scan_meta_yml(path)
    for pathpair in pathpairs:
        db.add_pathpair(pathpair)


@main.command(help="Update database continiously, watches for new or changed files.")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def watch(path, db_path, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    print("starting...")
    i = inotify.adapters.InotifyTree(path)
    if db_path is None:
        db_path = path + "/.pathtraits.db"
    db = TraitsDB(db_path)
    print("ready")

    for event in i.event_gen(yield_nones=False):
        (_, type_names, dir_path, filename) = event

        if not type_names.__contains__("IN_CLOSE_WRITE"):
            continue

        # watch afor both yml and object files
        # yml file might be created first and will be ignored
        path = os.path.join(dir_path, filename)
        pair = PathPair.find(path)
        if pair:
            db.add_pathpair(pair)


@main.command(help="Get traits of a given path")
@click.argument("path", required=True, type=click.Path(exists=True))
@click.option(
    "--db-path",
    default=None,
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option("-v", "--verbose", flag_value=True, default=False)
def get(path, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    abs_path = os.path.abspath(path)
    leaf_dir = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path
    dirs = leaf_dir.split("/")

    if db_path is None:
        db_path = path + "/.pathtraits.db"
        db = TraitsDB(db_path)
    else:
        # find db path
        found_db = False
        for i in reversed(range(0, len(dirs))):
            if i == 0:
                db_dir = "/"
            else:
                db_dir = "/".join(dirs[0 : i + 1])

            db_path = db_dir + "/.pathtraits.db"

            if os.path.exists(db_path):
                db = TraitsDB(db_dir)
                found_db = True
                logging.debug(f"Found TraitsDB at {db_path}")
                break
            else:
                continue
        if not found_db:
            return Exception(
                f"No pathtraits database found for {abs_path} and its parents."
            )

    # get traits from path and its parents
    dirs_data = []
    data = db.get("data", path=abs_path)
    if data:
        dirs_data.append(data)
    for i in reversed(range(0, len(dirs))):
        cur_path = "/".join(dirs[0 : i + 1])
        data = db.get("data", path=cur_path)
        if data:
            dirs_data.append(data)

    # inherit traits: children overwrite parent path traits
    res = {}
    for cur_data in reversed(dirs_data):
        for k, v in cur_data.items():
            if v and k != "path":
                res[k] = v

    # output
    if len(res) > 0:
        print(yaml.safe_dump(res))
    else:
        print(f"No traits found for path {path}", file=sys.stderr)
    return


if __name__ == "__main__":
    main()
