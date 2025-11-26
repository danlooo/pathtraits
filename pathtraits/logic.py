import re
import os
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathPair:
    """
    A file and its side car meta data
    """

    object_path: str
    meta_path: str

    @staticmethod
    def find(path):
        logger.debug(f"find path: {path}")

        object_path = None
        meta_path = None

        yaml_re = re.compile(r"(\.)?(meta)?\.(yaml|yml)$")
        path_is_meta = yaml_re.search(path)

        if path_is_meta:
            meta_path = path
            object_path = re.sub(yaml_re, "", path)
            return PathPair(object_path, meta_path)
        else:
            object_path = path
            for p in [
                "meta.yml",
                "meta.yaml",
                ".meta.yml",
                ".meta.yaml",
                ".yml",
                ".yaml",
            ]:
                meta_path = os.path.join(object_path, p)
                if os.path.exists(meta_path):
                    return PathPair(object_path, meta_path)
        return None
