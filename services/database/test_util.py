import unittest

import util
from services.proto import database_pb2


class UtilTest(unittest.TestCase):

    def test_equivalent_filter(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.equivalent_filter(entry)
        self.assertEqual(clause, "title = ?")
        self.assertEqual(vals, ["Despacito"])

    def test_equivalent_filter_defaults(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.equivalent_filter(
            entry, defaults=[('body', 'cool')])
        self.assertIn("title = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("Despacito", vals)
        self.assertIn("cool", vals)

    def test_equivalent_filter_defaults_allow_overwrite(self):
        entry = database_pb2.PostsEntry(title="Despacito", body="dank")
        clause, vals = util.equivalent_filter(
            entry, defaults=[('body', 'cool')])
        self.assertIn("title = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("Despacito", vals)
        self.assertIn("dank", vals)
        self.assertNotIn("cool", vals)

    def test_not_equivalent_filter(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.not_equivalent_filter(entry)
        self.assertEqual(clause, 'title IS NOT ""')
        self.assertEqual(vals, ["Despacito"])

    def test_not_equivalent_filter_defaults(self):
        entry = database_pb2.PostsEntry(title="Despacito")
        clause, vals = util.not_equivalent_filter(
            entry, defaults=[('body', 'cool')])
        self.assertIn('title IS NOT ""', clause)
        self.assertIn("AND", clause)
        self.assertIn('body IS NOT ""', clause)
        self.assertIn("Despacito", vals)
        self.assertIn("cool", vals)
