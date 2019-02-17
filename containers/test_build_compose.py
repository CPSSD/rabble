import unittest

from build_compose import replace_vars

class BuildComposeTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_single_var(self):
        config = "who's a good boy? [[GOOD_BOY]] is!"
        environ = {"RABBLE_GOOD_BOY": "Noah"}
        rep = replace_vars(config, environ)
        self.assertEqual(rep, "who's a good boy? Noah is!")

    def test_repeated_var(self):
        config = "it's a [[ADJ]], [[ADJ]] world"
        environ = {"RABBLE_ADJ": "mad"}
        rep = replace_vars(config, environ)
        self.assertEqual(rep, "it's a mad, mad world")

    def test_multi_vars(self):
        config = "A = [[A]]\nB = [[B]]"
        environ = {"RABBLE_A": "a", "RABBLE_B": "b"}
        rep = replace_vars(config, environ)
        self.assertEqual(rep, "A = a\nB = b")

    def test_missing_var(self):
        with self.assertRaises(ValueError):
            replace_vars("this = [[A]]", {})


