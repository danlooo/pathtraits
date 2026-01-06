# pylint: disable-all

"""
Test module
"""

import os
import unittest
import tempfile
import pathtraits.db
import pathtraits.scan
import pathtraits.access


class TestMain(unittest.TestCase):
    db_path = None
    db = None

    @classmethod
    def setUpClass(cls):
        cls.db_path = tempfile.mkstemp()[1]
        pathtraits.scan.batch("test/example", cls.db_path, "North_America$", False)
        cls.db = pathtraits.db.TraitsDB(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.db_path)

    def test_db_exist(self):
        self.assertTrue(self.db is not None)

    def test_de(self):
        source = pathtraits.access.get_dict(self.db, "test/example/EU/de.txt")
        target = {
            "description": "Germany data",
            "has_sidecar_meta_file": True,
            "is_example": True,
            "score": "zero",
        }
        for k, v in target.items():
            self.assertEqual(source[k], v)

    def test_eu(self):
        source = pathtraits.access.get_dict(self.db, "test/example/EU")
        target = {
            "description": "EU data",
            "is_example": True,
            "score": 3.5,
            "users": ["dloos", "fgans"],
            "foo": {"bar": {"a": 1, "b": 2, "c": [1, 2, 3]}},
        }
        for k, v in target.items():
            self.assertEqual(source[k], v)

    def test_example(self):
        source = pathtraits.access.get_dict(self.db, "test/example")
        target = {
            "description": "all data",
            "is_example": True,
            "score": 5,
        }
        for k, v in target.items():
            self.assertEqual(source[k], v)

    def test_missing_north_america(self):
        source = pathtraits.access.get_dict(
            self.db, "test/example/Americas/North_America"
        )
        target = pathtraits.access.get_dict(self.db, "test/example/Americas")
        for k, v in target.items():
            self.assertEqual(source[k], v)

    def test_data_view(self):
        source = len(self.db.execute("SELECT * FROM data;").fetchall())
        target = 8
        self.assertEqual(source, target)


if __name__ == "__main__":
    unittest.main()
