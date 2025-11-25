import sqlite3
import os
import yaml
from pathtraits.logic import *
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class TraitsDB:
    cursor = None
    traits = []

    def __init__(self, path):
        db_path = os.path.join(path, ".pathtraits.db")
        self.cursor = sqlite3.connect(db_path, autocommit=True).cursor()

        init_path_table_query = """
            CREATE TABLE IF NOT EXISTS path (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path text NOT NULL 
            );
        """
        self.execute(init_path_table_query)

        init_path_index_query = """
            CREATE INDEX IF NOT EXISTS idx_path_path
            ON path(path);
        """
        self.execute(init_path_index_query)
        self.update_traits()

    def execute(self, query):
        logger.debug(query)
        res = self.cursor.execute(query)
        return res

    def get(self, table, cols="*", condition=None, **kwargs):
        if not condition:
            escaped_kwargs = {
                k: v if type(v) != str else f"'{v}'" for (k, v) in kwargs.items()
            }
            condition = " AND ".join([f"{k}={v}" for (k, v) in escaped_kwargs.items()])
        get_row_query = f"SELECT {cols} FROM {table} WHERE {condition} LIMIT 1;"
        res = self.execute(get_row_query).fetchone()
        return res

    def put_path_id(self, path):
        get_row_query = f"SELECT id FROM path WHERE path = '{path}' LIMIT 1;"
        res = self.execute(get_row_query).fetchone()
        if res:
            return res[0]
        else:
            # create
            self.put("path", path=path)
            path_id = self.get("path", path=path, cols="id")[0]
            return path_id

    def escape(value):
        if type(value) == str:
            return f"'{value}'"
        if type(value) == bool:
            return "TRUE" if value else "FALSE"
        return value

    def put(self, table, condition="TRUE", **kwargs):
        """
        Puts a row into a table. Creates a row if not present, updates otherwise.
        """
        escaped_kwargs = {k: TraitsDB.escape(v) for (k, v) in kwargs.items()}

        if self.get(table, condition=condition, **kwargs):
            # update
            values = " , ".join([f"{k}={v}" for (k, v) in escaped_kwargs.items()])
            update_query = f"UPDATE {table} SET {values} WHERE {condition};"
            self.execute(update_query)
        else:
            # insert
            keys = " , ".join(escaped_kwargs.keys())
            values = " , ".join([str(x) for x in escaped_kwargs.values()])
            insert_query = f"INSERT INTO {table} ({keys}) VALUES ({values});"
            self.execute(insert_query)

    def update_traits(self):
        get_traits_query = """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
         """
        traits = self.execute(get_traits_query).fetchall()
        self.traits = [x[0] for x in traits]

    def create_trait_table(self, key, col_type):
        if key in self.traits:
            return
        sqlite_types = {
            bool: "BOOL",
            int: "INTEGER",
            float: "REAL",
            str: "TEXT",
        }
        if col_type == list:
            logger.debug(f"ignore list trait {key}")
            return
        if col_type == dict:
            logger.debug(f"ignore dict trait {key}")
            return
        col_type = sqlite_types.get(col_type, "TEXT")
        add_table_query = f"""
            CREATE TABLE {key} (
                path INTEGER,
                {key} {col_type},
                FOREIGN KEY(path) REFERENCES path(id)
            );
        """
        self.execute(add_table_query)
        self.update_traits()

    def put_trait(self, path_id, key, value):
        kwargs = {"path": path_id, key: value}
        self.put(key, condition=f"path = {path_id}", **kwargs)

    def add_pathpair(self, pair: PathPair):
        path_id = self.put_path_id(pair.file_path)

        with open(pair.meta_path, "r") as f:
            traits = yaml.safe_load(f)
            if traits is None:
                return
            for k, v in traits.items():
                if k not in self.traits:
                    self.create_trait_table(k, type(v))
                if k in self.traits:
                    self.put_trait(path_id, k, v)
