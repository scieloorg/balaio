import unittest

from balaio import uploader


class LoadModuleTests(unittest.TestCase):

    def test_valid_module(self):
        import json
        json_2 = uploader.load_module('json')

        self.assertEqual(json, json_2)

    def test_invalid_module(self):
        self.assertRaises(ImportError,
            lambda: uploader.load_module('bacon'))


class BlobBackendTests(unittest.TestCase):
    pass

