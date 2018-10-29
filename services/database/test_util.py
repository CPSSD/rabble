import unittest

import util
import database_pb2

class UtilTest(unittest.TestCase):
    def test_entry_to_filter(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.entry_to_filter(entry)
        self.assertEqual(clause, "title = ?")
        self.assertEqual(vals, ["Despacito"])

