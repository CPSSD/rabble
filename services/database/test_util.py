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

    def test_equivalent_filter_deferred(self):
        entry = database_pb2.PostsEntry(
                title="Despacito",
                body="alexa",
        )

        d = {'body': lambda entry, comp: ("body" + comp, True)}

        clause, vals = util.equivalent_filter(entry, deferred=d)
        self.assertIn("title = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("Despacito", vals)
        self.assertIn(True, vals)
        self.assertNotIn("alexa", vals)

    def test_equivalent_filter_deferred_default_unset(self):
        entry = database_pb2.PostsEntry(
                title="Despacito",
        )

        d = {'body': lambda entry, comp: ("body" + comp, True)}
        de = [('body', False)]

        clause, vals = util.equivalent_filter(entry, defaults=de, deferred=d)
        self.assertIn("title = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("Despacito", vals)
        self.assertIn(False, vals)

    def test_equivalent_filter_deferred_default_set(self):
        entry = database_pb2.PostsEntry(
                title="Despacito",
                body="nice"
        )

        d = {'body': lambda entry, comp: ("body" + comp, True)}
        de = [('body', False)]

        clause, vals = util.equivalent_filter(entry, defaults=de, deferred=d)
        self.assertIn("title = ?", clause)
        self.assertIn("AND", clause)
        self.assertIn("body = ?", clause)
        self.assertIn("Despacito", vals)
        self.assertIn(True, vals)
        self.assertNotIn(False, vals)
        self.assertNotIn("nice", vals)

    def test_update_filter(self):
        entry = database_pb2.PostsEntry(
                title="Megolavania",
                body="sans is angry",
        )
        clause, vals = util.entry_to_update(entry)
        self.assertIn('title = ?', clause)
        self.assertIn(', ', clause)
        self.assertIn('body = ?', clause)
        self.assertIn("Megolavania", vals)
        self.assertIn("sans is angry", vals)

    def test_update_filter_deferred_none_return(self):
        entry = database_pb2.PostsEntry(
                title="Megolavania",
                body="sans is angry",
        )
        d = {'body': lambda entry, comp: ("", util.DONT_USE_FIELD)}
        clause, vals = util.entry_to_update(entry, deferred=d)
        self.assertIn('title = ?', clause)
        self.assertNotIn('body = ?', clause)
        self.assertNotIn("sans is angry", vals)

    def test_update_filter_deferred_value_set(self):
        entry = database_pb2.PostsEntry(
                title="Megolavania",
                body="sans is angry",
        )
        d = {'body': lambda entry, comp: ("body" + comp, True)}
        clause, vals = util.entry_to_update(entry, deferred=d)
        self.assertIn('title = ?', clause)
        self.assertIn(', ', clause)
        self.assertIn('body = ?', clause)
        self.assertIn("Megolavania", vals)
        self.assertIn(True, vals)

    def test_update_filter_deferred_unset(self):
        entry = database_pb2.PostsEntry(
                title="Megolavania",
        )
        d = {'body': lambda entry, comp: ("body" + comp, True)}
        clause, vals = util.entry_to_update(entry, deferred=d)
        self.assertIn('title = ?', clause)
        self.assertIn("Megolavania", vals)
