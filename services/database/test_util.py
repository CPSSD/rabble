import unittest

import util
from services.proto import database_pb2

class UtilTest(unittest.TestCase):
    def test_entry_to_filter(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.entry_to_filter(entry)
        self.assertEqual(clause, "title = ?")
        self.assertEqual(vals, ["Despacito"])

    def test_entry_to_filter_defaults(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.entry_to_filter(entry, defaults=[('body', 'cool')])
        self.assertIn("title = ?", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("Despacito", vals)
        self.assertIn("cool", vals)

    def test_entry_to_filter_defaults_allow_overwrite(self):
        entry = database_pb2.PostsEntry(title="Despacito", body="dank")
        clause, vals = util.entry_to_filter(entry, defaults=[('body', 'cool')])
        self.assertIn("title = ?", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("Despacito", vals)
        self.assertIn("dank", vals)
        self.assertNotIn("cool", vals)
