"""
Module to handle the traits database
"""

import logging
import sqlite3
import os
import sys
from collections.abc import MutableMapping
import yaml
from pathtraits.pathpair import PathPair

logger = logging.getLogger(__name__)


class TraitsDB:
    """
    Database of pathtrait in 3NF with view of all joined trait tables
    """

    cursor = None
    traits = []

    @staticmethod
    def remove_type_suffixes(s: str):
        """
        Docstring for remove_type_suffixes

        :param s: Description
        :type s: str
        """
        s = s.removesuffix("_TEXT").removesuffix("_REAL").removesuffix("_BOOL")
        return s

    @staticmethod
    def row_factory(cursor, row):
        """
        Turns sqlite3 row into a dict. Only works on a single row at once.

        :param cursor: Description
        :param row: Description
        """
        fields = [column[0] for column in cursor.description]
        res = {}
        for k, v in zip(fields, row):
            if v is None:
                continue
            # sqlite don't know bool
            if k.endswith("_BOOL"):
                v = v > 0
            if isinstance(v, float):
                v_int = int(v)
                v = v_int if v_int == v else v
            k = TraitsDB.remove_type_suffixes(k)
            res[k] = v
        return res

    @staticmethod
    def merge_rows(rows: list):
        """
        Merges a list of row dicts of a path into a sinle dict by pooling trait keys

        :param res: Description
        """
        res = {}
        for row in rows:
            for k, v in row.items():
                # pylint: disable=C0201
                if not k in res.keys():
                    res[k] = []
                if not v in res[k]:
                    res[k].append(v)

        # simplify lists with just one element
        # ensure fixed order of list entries
        res = {k: sorted(v, key=str) if len(v) > 1 else v[0] for k, v in res.items()}
        return res

    @staticmethod
    def flatten_dict(dictionary: dict, root_key: str = "", separator: str = "/"):
        """
        Docstring for flatten_dict

        :param d: Description
        :type d: dict
        """
        items = []
        for key, value in dictionary.items():
            new_key = str(root_key) + str(separator) + str(key) if root_key else key
            if isinstance(value, MutableMapping):
                items.extend(
                    TraitsDB.flatten_dict(value, new_key, separator=separator).items()
                )
            else:
                items.append((new_key, value))
        return dict(items)

    def __init__(self, db_path):
        db_path = os.path.join(db_path)
        self.cursor = sqlite3.connect(db_path, autocommit=True).cursor()
        self.cursor.row_factory = TraitsDB.row_factory

        init_path_table_query = """
            CREATE TABLE IF NOT EXISTS _path (
                path_id INTEGER PRIMARY KEY AUTOINCREMENT,
                path text NOT NULL UNIQUE
            );
        """
        self.execute(init_path_table_query)

        init_path_index_query = """
            CREATE INDEX IF NOT EXISTS idx_path_path
            ON _path(path);
        """
        self.execute(init_path_index_query)

        init_trait_table_query = """
            CREATE TABLE IF NOT EXISTS _trait (
                trait_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait text NOT NULL UNIQUE
            );
        """
        self.execute(init_trait_table_query)

        init_trait_path_table_query = """
            CREATE TABLE IF NOT EXISTS _trait_path (
                trait_id INTEGER,
                path_id INTEGER,
                FOREIGN KEY(trait_id) REFERENCES _trait(trait_id),
                FOREIGN KEY(path_id) REFERENCES path(path_id),
                UNIQUE(trait_id, path_id)
            );
        """
        self.execute(init_trait_path_table_query)

        self.update_trait()

    # pylint: disable=R1710
    def execute(self, query, ignore_error=True):
        """
        Execute a SQLite query

        :param self: this database
        :param query: SQLite query string
        """
        try:
            res = self.cursor.execute(query)
            return res
        except sqlite3.DatabaseError as e:
            if ignore_error:
                logger.debug("Ignore failed query %s: %s", query, e)
            else:
                sys.exit(e)

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
        get_row_query = f"SELECT {cols} FROM [{table}] WHERE {condition};"
        response = self.execute(get_row_query)

        if response is None:
            return None

        res = response.fetchall()
        if len(res) == 1:
            return res[0]

        if isinstance(res, list) and len(res) > 1:
            res = TraitsDB.merge_rows(res)

        return res

    def get_path_id(self, path: str):
        """
        Docstring for get_path_id

        :param self: Description
        :param path: Description
        :type path: str
        """
        res = self.get("_path", path=path, cols="path_id")
        if res == []:
            return None

        return res["path_id"]

    def get_traits(self, path_id: int):
        """
        Get traits of a given path
        """
        query = f"""
        SELECT DISTINCT trait
        FROM _trait
        INNER JOIN _trait_path
        WHERE path_id = '{path_id}'
        """
        response = self.execute(query)

        if response is None:
            return None

        res = response.fetchall()
        if len(res) == 1:
            return res[0]
        return [x["trait"] for x in res]

    def get_pathtraits(self, path: str):
        """
        Docstring for get_pathtraits

        :param self: Description
        :param path: Description
        :type path: str
        """
        path_id = self.get_path_id(path)
        traits = self.get_traits(path_id)
        res = {}
        for trait in traits:
            pathtraits = self.get(trait, path_id=path_id)
            if isinstance(pathtraits, dict):
                pathtraits.pop("path_id")
                for k, v in pathtraits.items():
                    res[k] = v
        return res

    def get_paths(self, query_str):
        """
        Get paths matching pathtraits

        :param self: Description
        :param kwargs: pathtraits to match
        """
        traits = filter(lambda x: x in query_str, self.traits)
        query = "SELECT DISTINCT path FROM _path"
        for trait in traits:
            # pylint: disable=R1713
            query += f" NATURAL JOIN {trait}"
        query += f" WHERE {query_str};"

        response = self.execute(query)
        if response is None:
            return None

        res = response.fetchall()
        res = [x["path"] for x in res]
        return res

    def put_path_id(self, path):
        """
        Docstring for put_path_id

        :param self: this database
        :param path: path to put to the data base
        :returns: the id of that path
        """
        get_row_query = f"SELECT path_id FROM _path WHERE path = '{path}' LIMIT 1;"
        res = self.execute(get_row_query).fetchone()
        if res:
            return res["path_id"]
        # create
        self.put("_path", path=path)
        path_id = self.get_path_id(path)
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

    def put(self, table, condition=None, update=True, **kwargs):
        """
        Puts a row into a table. Creates a row if not present, updates otherwise.
        :param update; overwrite existing data
        """
        escaped_kwargs = {k: TraitsDB.escape(v) for (k, v) in kwargs.items()}

        if update and self.get(table, condition=condition, **kwargs):
            # update
            values = " , ".join([f"[{k}]={v}" for (k, v) in escaped_kwargs.items()])
            if condition:
                update_query = f"UPDATE [{table}] SET {values} WHERE {condition};"
            else:
                update_query = f"UPDATE [{table}] SET {values};"
            self.execute(update_query)
        else:
            # insert
            keys = "[" + "], [".join(escaped_kwargs.keys()) + "]"
            values = " , ".join([str(x) for x in escaped_kwargs.values()])
            insert_query = f"INSERT INTO [{table}] ({keys}) VALUES ({values});"
            self.execute(insert_query)

    def update_trait(self):
        """
        Get all traits from the database
        """
        get_trait_query = """
            SELECT trait
            FROM _trait
            ORDER BY trait;
         """
        traits = self.execute(get_trait_query)
        if traits is not None:
            traits = traits.fetchall()
        else:
            traits = []
        self.traits = [list(x.values())[0] for x in traits]

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
            CREATE TABLE [{trait_name}] (
                path_id INTEGER,
                [{trait_name}] {sql_type},
                FOREIGN KEY(path_id) REFERENCES path(path_id)
            );
        """
        self.execute(add_table_query)
        self.put("_trait", trait=trait_name)
        self.update_trait()

    def put_trait(self, path_id, trait_name, value, update=True):
        """
        Put a trait to the database

        :param self: this database
        :param path_id: id of the path in the path table
        :param key: trait name
        :param value: trait value
        """
        kwargs = {"path_id": path_id, trait_name: value}
        trait_id = self.get("_trait", trait=trait_name)["trait_id"]
        self.put("_trait_path", trait_id=trait_id, path_id=path_id)
        self.put(trait_name, condition=f"path_id = {path_id}", update=update, **kwargs)

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

            traits = TraitsDB.flatten_dict(traits)

            # put path in db only if there are traits
            path_id = self.put_path_id(os.path.abspath(pair.object_path))
            for k, v in traits.items():
                # same YAML key might have different value types
                # Therefore, add type to key

                # get element type for list
                # add: handle lists with mixed element type
                t = type(v[0]) if isinstance(v, list) and len(v) > 0 else type(v)
                k = f"{k}_{TraitsDB.sql_type(t)}"
                if k not in self.traits:
                    self.create_trait_table(k, t)
                if k in self.traits:
                    # add to list
                    if isinstance(v, list):
                        for vv in v:
                            self.put_trait(path_id, k, vv, update=False)
                    # overwrite scalar
                    else:
                        self.put_trait(path_id, k, v)
