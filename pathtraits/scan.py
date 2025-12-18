import inotify.adapters
import os
import logging
from pathtraits.pathpair import *
from pathtraits.db import *

logger = logging.getLogger(__name__)


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
                    if e.name.endswith(yml_extension):
                        object_path = e.path.replace(f"{yml_extension}", "")
                        pair = PathPair(object_path, e.path)
                        yml_paths.append(pair)
                        logger.debug(f"found pathpair {pair}")
                        break
    return yml_paths


def batch(path, db_path, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if db_path is None:
        db_path = path + "/.pathtraits.db"
    db = TraitsDB(db_path)
    pathpairs = scan_meta_yml(path)
    for pathpair in pathpairs:
        db.add_pathpair(pathpair)


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
