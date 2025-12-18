import inotify.adapters
import os
import logging
from pathtraits.pathpair import *
from pathtraits.db import *
import re

logger = logging.getLogger(__name__)

yaml_re = re.compile(r"(\.)?(meta)?\.(yaml|yml)$")


def scan_meta_yml(path, pathpairs=[]):
    # faster than os.walk
    with os.scandir(path) as ents:
        for e in ents:
            if e.is_dir():
                scan_meta_yml(e.path, pathpairs)
            else:
                if not yaml_re.search(e.path):
                    continue
                object_path = re.sub(yaml_re, "", e.path)
                if not os.path.exists(object_path):
                    continue
                pair = PathPair(object_path, e.path)
                pathpairs.append(pair)
    return pathpairs


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
            logger.debug(f"add pathpair: {pair}")
            db.add_pathpair(pair)
