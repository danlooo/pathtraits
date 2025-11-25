import yaml
import re
import os
import pathlib
from dataclasses import dataclass


@dataclass
class PathPair:
    """
    A file and its side car meta data
    """

    file_path: str
    meta_path: str

    @staticmethod
    def find(path):
        file_path = None
        meta_path = None

        yaml_re = re.compile(r"\.(yaml|yml)$")
        path_is_meta = yaml_re.search(path)

        if path_is_meta:
            meta_path = path
            file_path = re.sub(yaml_re, "", path)
        else:
            meta_path = path + ".yml"
            file_path = path

        if os.path.exists(meta_path) and os.path.exists(file_path):
            return PathPair(file_path, meta_path)
        else:
            return None

    def to_row(self):
        with open(self.meta_path, "r") as f:
            d = yaml.safe_load(f)
            print(d)
        pass
