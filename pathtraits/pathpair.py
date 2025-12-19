"""
Module to describe a file and its side car meta data
"""

import logging
import re
import os
from dataclasses import dataclass

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
        """
        Find the object file and its side car meta data file.
        Will determine whether a side car file exists.
        Returns None if there is no corresponding meta data file or object file.

        :param path: any path
        """
        object_path = None
        meta_path = None

        yaml_re = re.compile(r"(\.)?(meta)?\.(yaml|yml)$")
        path_is_meta = yaml_re.search(path) and os.path.isfile(path)

        if path_is_meta:
            meta_path = path
            if os.path.isfile(path):
                object_path = re.sub(yaml_re, "", path)
            else:
                object_path = path
            return PathPair(object_path, meta_path)

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
