"""
Module for accessing path traits from the database.
"""

import os
import sys
import logging
import yaml
from pathtraits.db import TraitsDB

logger = logging.getLogger(__name__)


def nest_dict(flat_dict, delimiter="/"):
    """
    Transforms a flat dictionary with path-like keys into a nested dictionary.

    :param flat_dict: The flat dictionary with path-like keys.
    :param delimiter: The delimiter used in the keys (default is '/').
    :return: A nested dictionary.
    """
    nested_dict = {}

    for path, value in flat_dict.items():
        keys = path.split(delimiter)
        current = nested_dict

        for key in keys[:-1]:
            # If the key doesn't exist or is not a dictionary, create/overwrite it as a dictionary
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the value at the final key
        current[keys[-1]] = value

    return nested_dict


def get_dict(db, path):
    """
    Get traits for a path as a Python dictionary

    :param self: this database
    :param path: path to get traits for
    """
    abs_path = os.path.abspath(path)
    leaf_dir = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path
    dirs = leaf_dir.split("/")

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
            if not (v and k != "path"):
                continue
            res[k] = v
    res = nest_dict(res)
    return res


def get_paths(db, query_str):
    """
    Docstring for get_paths

    :param db: Description
    :param query_str: Description
    """
    query_str = f"SELECT DISTINCT path FROM data where {query_str};"
    res = db.execute(query_str, ignore_error=False).fetchall()
    res = [x["path"] for x in res]
    return res


def get_paths_values(db, query_str):
    """
    Docstring for get_paths_values

    :param db: Description
    :param query_str: Description
    """
    query_str = f"SELECT * FROM data where {query_str};"
    response = db.execute(query_str, ignore_error=False).fetchall()
    res = {}
    for r in response:
        path = r["path"]
        # ensure distinct paths
        if path not in res.keys():
            r = nest_dict(r)
            r.pop("path")
            res[path] = r
    return res


def get(path, db_path, verbose):
    """
    Docstring for get

    :param path: Description
    :param db_path: Description
    :param verbose: Description
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    db = TraitsDB(db_path)
    res = get_dict(db, path)
    if len(res) > 0:
        print(yaml.safe_dump(res))
    else:
        logger.error("No traits found for path %s in database %s", path, db_path)
        sys.exit(1)


def query(query_str, db_path, show_values):
    """
    Docstring for query

    :param query_str: Description
    :param db_path: Description
    """
    db = TraitsDB(db_path)
    if show_values:
        res = get_paths_values(db, query_str)
        if len(res) > 0:
            print(yaml.safe_dump(res))
        else:
            logger.error(
                "No paths found for traits matching %s in database %s",
                query_str,
                db_path,
            )
        sys.exit(1)
    else:
        res = get_paths(db, query_str)
        if len(res) > 0:
            for r in res:
                print(r)
        else:
            logger.error(
                "No paths found for traits matching %s in database %s",
                query_str,
                db_path,
            )
