"""
Module for accessing path traits from the database.
"""

import os
import sys
import logging
import yaml
from pathtraits.db import TraitsDB

logger = logging.getLogger(__name__)


def get_dict(self, path):
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
    data = self.get("data", path=abs_path)
    if data:
        dirs_data.append(data)
    for i in reversed(range(0, len(dirs))):
        cur_path = "/".join(dirs[0 : i + 1])
        data = self.get("data", path=cur_path)
        if data:
            dirs_data.append(data)

    # inherit traits: children overwrite parent path traits
    res = {}
    for cur_data in reversed(dirs_data):
        for k, v in cur_data.items():
            if v and k != "path":
                res[k] = v
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
