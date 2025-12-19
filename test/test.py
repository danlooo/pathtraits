# pylint: disable-all

"""
Test module
"""

import unittest
import tempfile
import pathtraits.db
import pathtraits.scan


class TestMain(unittest.TestCase):
    def test_example(self):
        db_path = tempfile.mkstemp()[1]
        pathtraits.scan.batch("test/example", db_path, False)

        db = pathtraits.db.TraitsDB(db_path)
        self.assertTrue(db is not None)

        source = db.get_dict("test/example/EU/de.txt")
        target = {
            "description_TEXT": "Germany data",
            "has_sidecar_meta_file_BOOL": 1,
            "is_example_BOOL": 1,
            "score_TEXT": "zero",
            "score_REAL": 3.5,
        }
        for k, v in target.items():
            self.assertEqual(source[k], v)

        source = len(db.execute("SELECT * FROM data;").fetchall())
        target = 4
        self.assertEqual(source, target)


if __name__ == "__main__":
    unittest.main()
