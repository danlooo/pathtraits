"""
Module for scanning directories
"""

import logging
import os
import re

import inotify.adapters
from pathtraits.pathpair import PathPair
from pathtraits.db import TraitsDB

logger = logging.getLogger(__name__)

yaml_re = re.compile(r"(\.)?(meta)?\.(yaml|yml)$")


# pylint: disable=W0102
def scan_meta_yml(path, pathpairs=[], exclude_regex=None):
    """
    Scan a directory recursively for meta yml files and return PathPairs.

    :param path: Root path to scan
    :param pathpairs: list of pathpairs found so far (used for recursion)
    """
    try:
        # faster than os.walk
        with os.scandir(path) as ents:
            for e in ents:
                if not exclude_regex is None:
                    if exclude_regex.search(e.path):
                        logger.debug("exclude subtree path: %s", e.path)
                        continue
                if e.is_dir():
                    scan_meta_yml(e.path, pathpairs, exclude_regex)
                else:
                    if not yaml_re.search(e.path):
                        continue
                    object_path = re.sub(yaml_re, "", e.path)
                    if not os.path.exists(object_path):
                        continue
                    pair = PathPair(object_path, e.path)
                    pathpairs.append(pair)
        return pathpairs
    except (FileNotFoundError, PermissionError, OSError) as ex:
        logger.error("skip %s: %s", path, ex)
        return pathpairs


def batch(path, db_path, exclude_regex, verbose):
    """
    Update database once, searches for all directories recursively.

    :param path: path to scan in batch mode recursively
    :param db_path: path to the database
    :param verbose: enable verbose logging
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if db_path is None:
        db_path = path + "/.pathtraits.db"
    db = TraitsDB(db_path)
    if exclude_regex is not None:
        exclude_regex = re.compile(exclude_regex)
    pathpairs = scan_meta_yml(path, exclude_regex=exclude_regex)
    for pathpair in pathpairs:
        db.add_pathpair(pathpair)


def watch(path, db_path, verbose):
    """
    Update database continiously, watches for new or changed files.

    :param path: path to watch recursively
    :param db_path: path to the database
    :param verbose: enable verbose logging
    """
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

        if not type_names.contains("IN_CLOSE_WRITE"):
            continue

        # watch afor both yml and object files
        # yml file might be created first and will be ignored
        path = os.path.join(dir_path, filename)
        pair = PathPair.find(path)
        if pair:
            logger.debug("add pathpair: %s", pair)
            db.add_pathpair(pair)
