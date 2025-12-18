import os
import logging
import yaml
from pathtraits.db import TraitsDB

logger = logging.getLogger(__name__)


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
