# pylint: disable-all

"""
Test module
"""

import unittest
import tempfile
import pathtraits.db
import pathtraits.scan


class TestCLI(unittest.TestCase):
    def test(self):
        db_path = tempfile.mkstemp()[1]
        pathtraits.scan.batch("test/example", db_path, False)

        db = pathtraits.db.TraitsDB(db_path)
        self.assertTrue(db is not None)


if __name__ == "__main__":
    unittest.main()
