"""
Module to handle the traits database
"""

import logging
import sqlite3
import os
import yaml
from pathtraits.pathpair import PathPair

logger = logging.getLogger(__name__)


class TraitsDB:
    """
    Database of pathtrait in 3NF with view of all joined trait tables
    """

    cursor = None
    traits = []

    def __init__(self, db_path):
        db_path = os.path.join(db_path)
        self.cursor = sqlite3.connect(db_path, autocommit=True).cursor()

        init_path_table_query = """
            CREATE TABLE IF NOT EXISTS path (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path text NOT NULL UNIQUE
            );
        """
        self.execute(init_path_table_query)

        init_path_index_query = """
            CREATE INDEX IF NOT EXISTS idx_path_path
            ON path(path);
        """
        self.execute(init_path_index_query)
        self.update_traits()

    # pylint: disable=R1710
    def execute(self, query):
        """
        Execute a SQLite query

        :param self: this database
        :param query: SQLite query string
        """
        try:
            res = self.cursor.execute(query)
            return res
        except sqlite3.DatabaseError:
            logger.debug("Ignore failed query %s", query)

    def get(self, table, cols="*", condition=None, **kwargs):
        """
        Get a row from a table

        :param self: this database
        :param table: table name
        :param cols: colums to get as a string to be put after SELECT. All by default.
        :param condition: SQL condition string to be put after WHERE. Will overweite kwargs
        """
        if not condition:
            escaped_kwargs = {
                k: v if not isinstance(v, str) else f"'{v}'"
                for (k, v) in kwargs.items()
            }
            condition = " AND ".join([f"{k}={v}" for (k, v) in escaped_kwargs.items()])
        get_row_query = f"SELECT {cols} FROM {table} WHERE {condition} LIMIT 1;"
        response = self.execute(get_row_query)
        values = response.fetchone()

        if values is None:
            return None

        keys = map(lambda x: x[0], response.description)
        res = dict(zip(keys, values))
        return res

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

    def put_path_id(self, path):
        """
        Docstring for put_path_id

        :param self: this database
        :param path: path to put to the data base
        :returns: the id of that path
        """
        get_row_query = f"SELECT id FROM path WHERE path = '{path}' LIMIT 1;"
        res = self.execute(get_row_query).fetchone()
        if res:
            return res[0]
        # create
        self.put("path", path=path)
        path_id = self.get("path", path=path, cols="id")["id"]
        return path_id

    @staticmethod
    def escape(value):
        """
        Escape a python value for SQL insertion

        :param value: value to be escaped
        """
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return value

    @staticmethod
    # pylint: disable=R1710
    def sql_type(value_type):
        """
        Translate a Python type to a SQLite type

        :param value_type: python type to translate
        """
        if value_type == list:
            return
        if value_type == dict:
            return

        sqlite_types = {
            bool: "BOOL",
            int: "REAL",
            float: "REAL",
            str: "TEXT",
        }
        sql_type = sqlite_types.get(value_type, "TEXT")
        return sql_type

    def put(self, table, condition=None, **kwargs):
        """
        Puts a row into a table. Creates a row if not present, updates otherwise.
        """
        escaped_kwargs = {k: TraitsDB.escape(v) for (k, v) in kwargs.items()}

        if self.get(table, condition=condition, **kwargs):
            # update
            values = " , ".join([f"{k}={v}" for (k, v) in escaped_kwargs.items()])
            if condition:
                update_query = f"UPDATE {table} SET {values} WHERE {condition};"
            else:
                update_query = f"UPDATE {table} SET {values};"
            self.execute(update_query)
        else:
            # insert
            keys = " , ".join(escaped_kwargs.keys())
            values = " , ".join([str(x) for x in escaped_kwargs.values()])
            insert_query = f"INSERT INTO {table} ({keys}) VALUES ({values});"
            self.execute(insert_query)

    def put_data_view(self):
        """
        Creates a SQL View with all denormalized traits
        """
        self.execute("DROP VIEW IF EXISTS DATA;")

        if self.traits:
            join_query = " ".join(
                [
                    f"LEFT JOIN {x} ON {x}.path = path.id"
                    for x in self.traits
                    if x != "path"
                ]
            )

            create_view_query = f"""
                CREATE VIEW data AS
                SELECT path.path, {', '.join(self.traits)}
                FROM path
                {join_query};
            """
        else:
            create_view_query = """
                CREATE VIEW data AS
                SELECT path.path
                FROM path;
            """
        self.execute(create_view_query)

    def update_traits(self):
        """
        Get all traits from the database
        """
        get_traits_query = """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            AND name != 'path'
            ORDER BY name;
         """
        traits = self.execute(get_traits_query).fetchall()
        self.traits = [x[0] for x in traits]
        self.put_data_view()

    def create_trait_table(self, trait_name, value_type):
        """
        Create a trait table if it does not exist

        :param self: this database
        :param key: trait name
        :param value_type: trait value
        """
        if trait_name in self.traits:
            return
        if value_type == list:
            logger.debug("ignore list trait %s", trait_name)
            return
        if value_type == dict:
            logger.debug("ignore dict trait %s", trait_name)
            return
        sql_type = TraitsDB.sql_type(value_type)
        add_table_query = f"""
            CREATE TABLE {trait_name} (
                path INTEGER,
                {trait_name} {sql_type},
                FOREIGN KEY(path) REFERENCES path(id)
            );
        """
        self.execute(add_table_query)
        self.update_traits()

    def put_trait(self, path_id, trait_name, value):
        """
        Put a trait to the database

        :param self: this database
        :param path_id: id of the path in the path table
        :param key: trait name
        :param value: trait value
        """
        kwargs = {"path": path_id, trait_name: value}
        self.put(trait_name, condition=f"path = {path_id}", **kwargs)

    def add_pathpair(self, pair: PathPair):
        """
        Add a PathPair to the database

        :param self: this database
        :param pair: the pathpair to be added
        :type pair: PathPair
        """
        with open(pair.meta_path, "r", encoding="utf-8") as f:
            try:
                traits = yaml.safe_load(f)
            except (yaml.YAMLError, OSError) as e:
                logging.debug("ignore meta file %s. Error message: %s", f, e)
                return

            # invalid trait yml file e.g. empty or no key-value pair
            if not isinstance(traits, dict):
                return

            # put path in db only if there are traits
            path_id = self.put_path_id(os.path.abspath(pair.object_path))
            for k, v in traits.items():
                # same YAML key might have different value types
                # Therefore, add type to key
                k = f"{k}_{TraitsDB.sql_type(type(v))}"
                if k not in self.traits:
                    self.create_trait_table(k, type(v))
                if k in self.traits:
                    self.put_trait(path_id, k, v)
