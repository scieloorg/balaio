import unittest

from balaio import uploader


class LoadModuleTests(unittest.TestCase):

    def test_valid_module(self):
        import json
        json_2 = uploader.load_module('json')

        self.assertEqual(json, json_2)

    def test_invalid_module(self):
        self.assertIsNone(uploader.load_module('bacon'))


class BlobBackendTests(unittest.TestCase):

    def test_enabled_when_nothing_is_required(self):
        self.assertTrue(uploader.BlobBackend.enabled())

    def test_enabled_when_stdlib_is_required(self):
        class Foo(uploader.BlobBackend):
            requires = ['json']

            def connect(self): pass
            def set_target(self, path): pass
            def cleanup(self): pass

        self.assertTrue(Foo.enabled())

    def test_enabled_when_missing_dependency(self):
        class Foo(uploader.BlobBackend):
            requires = ['bacon']

            def connect(self): pass
            def set_target(self, path): pass
            def cleanup(self): pass

        self.assertFalse(Foo.enabled())

    def test_ValueError_if_missing_dependency(self):
        class Foo(uploader.BlobBackend):
            requires = ['bacon']

            def connect(self): pass
            def set_target(self, path): pass
            def cleanup(self): pass

        self.assertRaises(ValueError, lambda: Foo())

    def test_instantiation_of_enabled_backend(self):
        class Foo(uploader.BlobBackend):
            requires = ['json']

            def connect(self): pass
            def set_target(self, path): pass
            def cleanup(self): pass

        self.assertIsInstance(Foo(), Foo)

