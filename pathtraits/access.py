import os
import logging
import yaml
from pathtraits.db import TraitsDB

logger = logging.getLogger(__name__)


def get(path, db_path, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    db = TraitsDB(db_path)
    res = db.get_dict(path)
    if len(res) > 0:
        print(yaml.safe_dump(res))
    else:
        logger.error(f"No traits found for path {path} in database {db_path}")
        exit(1)
