import unittest

import mocker

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
            def cleanup(self): pass

        self.assertTrue(Foo.enabled())

    def test_enabled_when_missing_dependency(self):
        class Foo(uploader.BlobBackend):
            requires = ['bacon']

            def connect(self): pass
            def cleanup(self): pass

        self.assertFalse(Foo.enabled())

    def test_ValueError_if_missing_dependency(self):
        class Foo(uploader.BlobBackend):
            requires = ['bacon']

            def connect(self): pass
            def cleanup(self): pass

        self.assertRaises(ValueError, lambda: Foo())

    def test_instantiation_of_enabled_backend(self):
        class Foo(uploader.BlobBackend):
            requires = ['json']

            def connect(self): pass
            def cleanup(self): pass

        self.assertIsInstance(Foo(), Foo)


class StaticScieloBackendTests(mocker.MockerTestCase):

    def test_get_fqpath(self):
        st = uploader.StaticScieloBackend(u'some.user', u'some.pass',
            u'/var/www/journals')
        self.assertEqual(st._get_fqpath(u'/art1/foo.pdf'),
            u'/var/www/journals/art1/foo.pdf')

    def test_ensure_parent_dir(self):
        st = uploader.StaticScieloBackend(u'some.user', u'some.pass',
            u'/var/www/journals')

        mock_st = self.mocker.patch(st, spec=False)
        mock_st.sftp.mkdir(mocker.ANY)
        self.mocker.result(None)
        self.mocker.count(4)
        self.mocker.replay()

        st._ensure_parent_dir(u'/var/www/journals/art1/foo.pdf')

    def test_get_resource_uri(self):
        st = uploader.StaticScieloBackend(u'some.user', u'some.pass',
            u'/var/www/')

        self.assertEqual(st._get_resource_uri(u'/journals/art1/foo.pdf'),
            u'http://static.scielo.org/journals/art1/foo.pdf')

