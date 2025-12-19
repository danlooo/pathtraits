"""
Module for accessing path traits from the database.
"""

import sys
import logging
import yaml
from pathtraits.db import TraitsDB

logger = logging.getLogger(__name__)


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
    res = db.get_dict(path)
    if len(res) > 0:
        print(yaml.safe_dump(res))
    else:
        logger.error("No traits found for path %s in database %s", path, db_path)
        sys.exit(1)
