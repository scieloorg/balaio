#coding: utf-8
import json
import sys
import os
import unittest

# adding balaio package to path, to avoid some httpd imports to blow up.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound,HTTPAccepted, HTTPCreated
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from webtest import TestApp
import transaction

from balaio import models, httpd
from .doubles import *
from .utils import db_bootstrap, DB_READY
from . import modelfactories


SAMPLE_PACKAGE = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)),
    '..', '..', 'samples', '0042-9686-bwho-91-08-545.zip'))

global_engine = None


def setUpModule():
    """
    Initialize the database.
    """
    global global_engine
    try:
        global_engine = db_bootstrap()
    except OperationalError:
        # global_engine remains None, all db-bound testcases
        # need to test for DB_READY before run.
        pass


def _load_fixtures(obj_list):

    with transaction.manager:
        models.ScopedSession.add_all(obj_list)


@unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
class FunctionalAPITest(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        app = httpd.main(ConfigStub(), global_engine)
        self.testapp = TestApp(app)

    def tearDown(self):
        models.ScopedSession.remove()
        testing.tearDown()

    def test_root(self):
        resp = self.testapp.get('/', status=200)
        self.assertTrue('http server' in resp.body.lower())

    def test_GET_to_unavailable_resource(self):
        self.testapp.get('/api/v1/lokmshin/', status=404)


@unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
class AttemptFunctionalAPITest(unittest.TestCase):

    def setUp(self):
        self._loaded_fixtures = [self._makeOne() for i in range(3)]
        self.config = testing.setUp()

        app = httpd.main(ConfigStub(), global_engine)
        self.testapp = TestApp(app)

    def tearDown(self):
        transaction.abort()
        models.ScopedSession.remove()
        testing.tearDown()

    def _makeOne(self):
        import datetime
        attempt = modelfactories.AttemptFactory.create()
        attempt.started_at = datetime.datetime(2013, 10, 9, 16, 44, 29, 865787)
        return attempt

    def test_GET_to_available_resource(self):
        self.testapp.get('/api/v1/attempts/', status=200)

    def test_GET_to_one_attempt(self):
        attempt_id = self._loaded_fixtures[0].id
        attempt_checksum = self._loaded_fixtures[0].package_checksum
        articlepkg_id = self._loaded_fixtures[0].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/%s/' % attempt_id)

        expected = '''{"filepath": "/tmp/watch/xxx.zip",
                       "finished_at": null,
                       "articlepkg_id": %s,
                       "proceed_to_checkout": false,
                       "checkout_started_at": null,
                       "queued_checkout": null,
                       "is_valid": true,
                       "started_at": "2013-10-09 16:44:29.865787",
                       "id": %s,
                       "package_checksum": "%s",
                       "resource_uri": "/api/v1/attempts/%s/"}''' % (articlepkg_id, attempt_id, attempt_checksum, attempt_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts(self):
        attempt0_id = self._loaded_fixtures[0].id
        attempt0_checksum = self._loaded_fixtures[0].package_checksum
        articlepkg0_id = self._loaded_fixtures[0].articlepkg.id

        attempt1_id = self._loaded_fixtures[1].id
        attempt1_checksum = self._loaded_fixtures[1].package_checksum
        articlepkg1_id = self._loaded_fixtures[1].articlepkg.id

        attempt2_id = self._loaded_fixtures[2].id
        attempt2_checksum = self._loaded_fixtures[2].package_checksum
        articlepkg2_id = self._loaded_fixtures[2].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/')

        expected = '''{"meta": {"previous": null, "next": null, "total": 3, "limit": 20, "offset": 0},
                       "objects": [
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"},
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"},
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"}
                        ]
                    }''' % (articlepkg0_id, attempt0_id, attempt0_checksum, attempt0_id,
                            articlepkg1_id, attempt1_id, attempt1_checksum, attempt1_id,
                            articlepkg2_id, attempt2_id, attempt2_checksum, attempt2_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts_with_param_limit(self):
        attempt0_id = self._loaded_fixtures[0].id
        attempt0_checksum = self._loaded_fixtures[0].package_checksum
        articlepkg0_id = self._loaded_fixtures[0].articlepkg.id

        attempt1_id = self._loaded_fixtures[1].id
        attempt1_checksum = self._loaded_fixtures[1].package_checksum
        articlepkg1_id = self._loaded_fixtures[1].articlepkg.id

        attempt2_id = self._loaded_fixtures[2].id
        attempt2_checksum = self._loaded_fixtures[2].package_checksum
        articlepkg2_id = self._loaded_fixtures[2].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/?limit=45')

        expected = '''{"meta": {"previous": null, "next": null, "total": 3, "limit": 45, "offset": 0},
                       "objects": [
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"},
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"},
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"}
                    ]}'''% (articlepkg0_id, attempt0_id, attempt0_checksum, attempt0_id,
                            articlepkg1_id, attempt1_id, attempt1_checksum, attempt1_id,
                            articlepkg2_id, attempt2_id, attempt2_checksum, attempt2_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts_with_param_offset(self):
        self.maxDiff = None
        attempt1_id = self._loaded_fixtures[1].id
        attempt1_checksum = self._loaded_fixtures[1].package_checksum
        articlepkg1_id = self._loaded_fixtures[1].articlepkg.id

        attempt2_id = self._loaded_fixtures[2].id
        attempt2_checksum = self._loaded_fixtures[2].package_checksum
        articlepkg2_id = self._loaded_fixtures[2].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/?offset=1')

        expected = '''{"meta": {"previous": null, "next": null, "total": 3, "limit": 20, "offset": "1"},
                       "objects": [
                         {"filepath": "/tmp/watch/xxx.zip",
                          "finished_at": null,
                          "articlepkg_id": %s,
                          "is_valid": true,
                          "started_at": "2013-10-09 16:44:29.865787",
                          "id": %s,
                          "package_checksum": "%s",
                          "proceed_to_checkout": false,
                          "checkout_started_at": null,
                          "queued_checkout": null,
                          "resource_uri": "/api/v1/attempts/%s/"},
                         {"filepath": "/tmp/watch/xxx.zip",
                          "finished_at": null,
                          "articlepkg_id": %s,
                          "is_valid": true,
                          "started_at": "2013-10-09 16:44:29.865787",
                          "id": %s,
                          "package_checksum": "%s",
                          "proceed_to_checkout": false,
                          "checkout_started_at": null,
                          "queued_checkout": null,
                          "resource_uri": "/api/v1/attempts/%s/"}
                        ]}''' % (articlepkg1_id, attempt1_id, attempt1_checksum, attempt1_id,
                                 articlepkg2_id, attempt2_id, attempt2_checksum, attempt2_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts_with_param_offset_and_limit(self):
        res = self.testapp.get('/api/v1/attempts/?offset=4&limit=78')
        expected = '{"meta": {"previous": null, "next": null, "total": 3, "limit": 78, "offset": "4"}, "objects": []}'

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts_with_param_low_limit(self):
        attempt0_id = self._loaded_fixtures[0].id
        attempt0_checksum = self._loaded_fixtures[0].package_checksum
        articlepkg0_id = self._loaded_fixtures[0].articlepkg.id

        attempt1_id = self._loaded_fixtures[1].id
        attempt1_checksum = self._loaded_fixtures[1].package_checksum
        articlepkg1_id = self._loaded_fixtures[1].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/?limit=2')

        expected = '''{"meta": {"previous": null, "next": "/api/v1/attempts/?limit=2&offset=2", "total": 3, "limit": 2, "offset": 0},
                       "objects": [
                         {"filepath": "/tmp/watch/xxx.zip",
                          "finished_at": null,
                          "articlepkg_id": %s,
                          "is_valid": true,
                          "started_at": "2013-10-09 16:44:29.865787",
                          "id": %s,
                          "package_checksum": "%s",
                          "proceed_to_checkout": false,
                          "checkout_started_at": null,
                          "queued_checkout": null,
                          "resource_uri": "/api/v1/attempts/%s/"},
                         {"filepath": "/tmp/watch/xxx.zip",
                          "finished_at": null,
                          "articlepkg_id": %s,
                          "is_valid": true,
                          "started_at": "2013-10-09 16:44:29.865787",
                          "id": %s,
                          "package_checksum": "%s",
                          "proceed_to_checkout": false,
                          "checkout_started_at": null,
                          "queued_checkout": null,
                          "resource_uri": "/api/v1/attempts/%s/"}
                        ]}''' % (articlepkg0_id, attempt0_id, attempt0_checksum, attempt0_id,
                                 articlepkg1_id, attempt1_id, attempt1_checksum, attempt1_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts_with_param_low_offset_and_limit(self):
        attempt1_id = self._loaded_fixtures[1].id
        attempt1_checksum = self._loaded_fixtures[1].package_checksum
        articlepkg1_id = self._loaded_fixtures[1].articlepkg.id

        attempt2_id = self._loaded_fixtures[2].id
        attempt2_checksum = self._loaded_fixtures[2].package_checksum
        articlepkg2_id = self._loaded_fixtures[2].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/?limit=2&offset=1')

        expected = '''{"meta": {"previous": null, "next": "/api/v1/attempts/?limit=2&offset=3", "total": 3, "limit": 2, "offset": "1"},
                       "objects": [
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"},
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"}
                         ]}'''% (articlepkg1_id, attempt1_id, attempt1_checksum, attempt1_id,
                                 articlepkg2_id, attempt2_id, attempt2_checksum, attempt2_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_attempts_with_param_low_limit_and_offset(self):
        attempt2_id = self._loaded_fixtures[2].id
        attempt2_checksum = self._loaded_fixtures[2].package_checksum
        articlepkg2_id = self._loaded_fixtures[2].articlepkg.id

        res = self.testapp.get('/api/v1/attempts/?limit=1&offset=2')

        expected = '''{"meta": {"previous": "/api/v1/attempts/?limit=1&offset=1", "next": "/api/v1/attempts/?limit=1&offset=3", "total": 3, "limit": 1, "offset": "2"},
                       "objects": [
                           {"filepath": "/tmp/watch/xxx.zip",
                            "finished_at": null,
                            "articlepkg_id": %s,
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "is_valid": true,
                            "started_at": "2013-10-09 16:44:29.865787",
                            "id": %s,
                            "package_checksum": "%s",
                            "proceed_to_checkout": false,
                            "checkout_started_at": null,
                            "queued_checkout": null,
                            "resource_uri": "/api/v1/attempts/%s/"}
                         ]}''' % (articlepkg2_id, attempt2_id, attempt2_checksum, attempt2_id)

        self.assertEqual(json.loads(res.body), json.loads(expected))


@unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
class PackageFunctionalAPITest(unittest.TestCase):

    def setUp(self):
        self._loaded_fixtures = [self._makeOne() for i in range(3)]
        models.ScopedSession.flush()

        self.config = testing.setUp()
        app = httpd.main(ConfigStub(), global_engine)
        self.testapp = TestApp(app)

    def tearDown(self):
        transaction.abort()
        models.ScopedSession.remove()
        testing.tearDown()

    def _makeOne(self):
        article = modelfactories.ArticlePkgFactory.create()
        return article

    def test_GET_to_available_resource(self):
        self.testapp.get('/api/v1/packages/', status=200)

    def test_GET_to_one_package(self):
        articlepkg_id = self._loaded_fixtures[0].id
        articlepkg_aid = self._loaded_fixtures[0].aid

        res = self.testapp.get('/api/v1/packages/%s/' % articlepkg_id)

        expected = '''{"article_title": "Construction of a recombinant adenovirus...",
                       "issue_year": 1995,
                       "journal_title": "Associa... Brasileira",
                       "journal_pissn": "0100-879X",
                       "journal_eissn": "0100-879X",
                       "issue_suppl_number": null,
                       "attempts": [],
                       "issue_suppl_volume": null,
                       "issue_volume": "67",
                       "resource_uri": "/api/v1/packages/%s/",
                       "id": %s,
                       "aid": "%s",
                       "issue_number": "8"}''' % (articlepkg_id, articlepkg_id, articlepkg_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_packages(self):
        articlepkg0_id = self._loaded_fixtures[0].id
        articlepkg1_id = self._loaded_fixtures[1].id
        articlepkg2_id = self._loaded_fixtures[2].id

        articlepkg0_aid = self._loaded_fixtures[0].aid
        articlepkg1_aid = self._loaded_fixtures[1].aid
        articlepkg2_aid = self._loaded_fixtures[2].aid

        res = self.testapp.get('/api/v1/packages/')

        expected = '''{"meta": {"previous": null, "next": null, "total": 3, "limit": 20, "offset": 0},
                       "objects": [
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"}
                    ]}''' % (articlepkg0_id, articlepkg0_id, articlepkg0_aid,
                             articlepkg1_id, articlepkg1_id, articlepkg1_aid,
                             articlepkg2_id, articlepkg2_id, articlepkg2_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_packages_with_param_limit(self):
        articlepkg0_id = self._loaded_fixtures[0].id
        articlepkg1_id = self._loaded_fixtures[1].id
        articlepkg2_id = self._loaded_fixtures[2].id

        articlepkg0_aid = self._loaded_fixtures[0].aid
        articlepkg1_aid = self._loaded_fixtures[1].aid
        articlepkg2_aid = self._loaded_fixtures[2].aid

        res = self.testapp.get('/api/v1/packages/?limit=82')

        expected = '''{"meta": {"previous": null, "next": null, "total": 3, "limit": 82, "offset": 0},
                       "objects": [
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"}
                    ]}''' % (articlepkg0_id, articlepkg0_id, articlepkg0_aid,
                             articlepkg1_id, articlepkg1_id, articlepkg1_aid,
                             articlepkg2_id, articlepkg2_id, articlepkg2_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_packages_with_param_offset(self):
        articlepkg1_id = self._loaded_fixtures[1].id
        articlepkg2_id = self._loaded_fixtures[2].id

        articlepkg1_aid = self._loaded_fixtures[1].aid
        articlepkg2_aid = self._loaded_fixtures[2].aid

        res = self.testapp.get('/api/v1/packages/?offset=1')

        expected = '''{"meta": {"previous": null, "next": null, "total": 3, "limit": 20, "offset": "1"},
                       "objects": [
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"}
                    ]}''' % (articlepkg1_id, articlepkg1_id, articlepkg1_aid,
                             articlepkg2_id, articlepkg2_id, articlepkg2_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_packages_with_param_offset_and_limit(self):
        res = self.testapp.get('/api/v1/packages/?offset=4&limit=78')

        self.assertEqual(json.loads(res.body), json.loads('{"meta": {"previous": null, "next": null, "total": 3, "limit": 78, "offset": "4"}, "objects": []}'))

    def test_GET_to_packages_with_param_low_limit(self):
        articlepkg0_id = self._loaded_fixtures[0].id
        articlepkg1_id = self._loaded_fixtures[1].id

        articlepkg0_aid = self._loaded_fixtures[0].aid
        articlepkg1_aid = self._loaded_fixtures[1].aid

        res = self.testapp.get('/api/v1/packages/?limit=2')

        expected = '''{"meta": {"previous": null, "next": "/api/v1/packages/?limit=2&offset=2", "total": 3, "limit": 2, "offset": 0},
                       "objects": [
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"}
                    ]}''' % (articlepkg0_id, articlepkg0_id, articlepkg0_aid,
                             articlepkg1_id, articlepkg1_id, articlepkg1_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_packages_with_param_low_offset_and_limit(self):
        articlepkg1_id = self._loaded_fixtures[1].id
        articlepkg2_id = self._loaded_fixtures[2].id

        articlepkg1_aid = self._loaded_fixtures[1].aid
        articlepkg2_aid = self._loaded_fixtures[2].aid

        res = self.testapp.get('/api/v1/packages/?limit=2&offset=1')

        expected = '''{"meta": {"previous": null, "next": "/api/v1/packages/?limit=2&offset=3", "total": 3, "limit": 2, "offset": "1"},
                       "objects": [
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"},
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"}
                    ]}''' % (articlepkg1_id, articlepkg1_id, articlepkg1_aid,
                             articlepkg2_id, articlepkg2_id, articlepkg2_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))

    def test_GET_to_packages_with_param_low_limit_and_offset(self):
        articlepkg2_id = self._loaded_fixtures[2].id
        articlepkg2_aid = self._loaded_fixtures[2].aid

        res = self.testapp.get('/api/v1/packages/?limit=1&offset=2')

        expected = '''{"meta": {"previous": "/api/v1/packages/?limit=1&offset=1", "next": "/api/v1/packages/?limit=1&offset=3", "total": 3, "limit": 1, "offset": "2"},
                       "objects": [
                           {"article_title": "Construction of a recombinant adenovirus...",
                            "issue_year": 1995,
                            "journal_title": "Associa... Brasileira",
                            "journal_pissn": "0100-879X",
                            "journal_eissn": "0100-879X",
                            "issue_suppl_number": null,
                            "attempts": [],
                            "issue_suppl_volume": null,
                            "issue_volume": "67",
                            "resource_uri": "/api/v1/packages/%s/",
                            "id": %s,
                            "aid": "%s",
                            "issue_number": "8"}
                    ]}''' % (articlepkg2_id, articlepkg2_id, articlepkg2_aid)

        self.assertEqual(json.loads(res.body), json.loads(expected))


class AttemptsAPITest(unittest.TestCase):

    def setUp(self):
        self.req = testing.DummyRequest()
        self.req.registry.settings = {'http_server': {'version': 'v1'}}
        self.req.db = ObjectStub()
        self.req.db.query = QueryStub
        self.req.db.query.model = AttemptStub

    def test_view_attempts(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'filters': {'articlepkg_id': 1},
                    'total': 200,
                    'objects': [AttemptStub().to_dict(), AttemptStub().to_dict()]}

        self.req.params = {'limit': 20, 'offset': 0, 'articlepkg_id': 1}
        self.req.db.query.found = True

        self.assertEqual(
            httpd.attempts(self.req),
            expected)

    def test_view_attempts_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'filters': {'articlepkg_id': 1},
                    'total': 200,
                    'objects': []}

        self.req.params = {'limit': 20, 'offset': 0, 'articlepkg_id': 1}
        self.req.db.query.found = False

        self.assertEqual(
            httpd.attempts(self.req),
            expected)

    def test_view_attempt(self):
        expected = AttemptStub().to_dict()

        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}
        self.assertEqual(
            httpd.attempt(self.req),
            expected)

    def test_view_attempt_no_result(self):
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            httpd.attempt(self.req),
            HTTPNotFound
        )


class ArticlePkgAPITest(unittest.TestCase):

    def setUp(self):
        self.req = testing.DummyRequest()
        self.req.registry.settings = {'http_server': {'version': 'v1'}}
        self.req.db = ObjectStub()
        self.req.db.query = QueryStub
        self.req.db.query.model = ArticlePkgStub

    def test_view_packages(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'filters': {'journal_title': 'Journal of ...'},
                    'total': 200,
                    'objects': [ArticlePkgStub().to_dict(), ArticlePkgStub().to_dict()]}

        self.req.params = {'limit': 20, 'offset': 0, 'journal_title': 'Journal of ...'}
        self.req.db.query.found = True

        self.assertEqual(
            httpd.list_package(self.req),
            expected)

    def test_view_packages_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'filters': {'journal_title': 'Journal of ...'},
                    'total': 200,
                    'objects': []}
        self.req.params = {'limit': 20, 'offset': 0, 'journal_title': 'Journal of ...'}
        self.req.db.query.found = False

        self.assertEqual(
            httpd.list_package(self.req),
            expected)

    def test_view_package(self):
        expected = ArticlePkgStub().to_dict()

        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}

        self.assertEqual(
            httpd.package(self.req),
            expected)

    def test_view_package_no_result(self):
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            httpd.attempt(self.req),
            HTTPNotFound
        )


class QueryFiltersTest(unittest.TestCase):

    def test_get_query_filter(self):
        expected = {'journal_pissn': '0100-879X',
                    'journal_eissn': '0900-879X',
                    }

        request_params = {
                            'format': 'json',
                            'offset': 20,
                            'limit': 50,
                            'journal_pissn': '0100-879X',
                            'journal_eissn': '0900-879X',
                        }

        model = ArticlePkgStub

        self.assertEqual(
            expected,
            httpd.get_query_filters(model, request_params)
        )


@unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
class FilesAPITests(unittest.TestCase):

    def setUp(self):
        self._loaded_fixtures = [self._makeOne() for i in range(3)]
        self.config = testing.setUp()

        app = httpd.main(ConfigStub(), global_engine)
        self.testapp = TestApp(app)

    def tearDown(self):
        transaction.abort()
        models.ScopedSession.remove()
        testing.tearDown()

    def _makeOne(self):
        import datetime
        attempt = modelfactories.AttemptFactory.create(filepath=SAMPLE_PACKAGE)
        attempt.started_at = datetime.datetime(2013, 10, 9, 16, 44, 29, 865787)
        return attempt

    def test_GET_all_filenames(self):
        attempt = self._makeOne()
        self.testapp.get('/api/v1/files/%s/' % attempt.id, status=200)

    def test_list_package_members(self):
        attempt = self._makeOne()
        response = self.testapp.get('/api/v1/files/%s/' % attempt.id)

        self.assertEqual(response.body,
            json.dumps({'xml': ['0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml'],
                        'pdf': ['0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.pdf']}))

    def test_non_integer_attempt_id(self):
        response = self.testapp.get('/api/v1/files/nonid/', status=404)

    def test_non_existing_attempt_id(self):
        response = self.testapp.get('/api/v1/files/99999999/', status=404)

    def test_GET_specific_member(self):
        attempt = self._makeOne()

        self.testapp.get(
            '/api/v1/files/%s/target.zip/?file=0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml' % attempt.id,
            status=200)

    def test_GET_specific_member_content(self):
        import zipfile
        import StringIO
        attempt = self._makeOne()

        response = self.testapp.get(
            '/api/v1/files/%s/target.zip/?file=0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml' % attempt.id,
            status=200)

        zip_res = zipfile.ZipFile(StringIO.StringIO(response.body))
        self.assertEqual(zip_res.namelist(), ['0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml'])

    def test_GET_many_members_contents(self):
        import zipfile
        import StringIO
        attempt = self._makeOne()

        response = self.testapp.get(
            '/api/v1/files/%s/target.zip/?file=0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml&file=0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.pdf' % attempt.id,
            status=200)

        zip_res = zipfile.ZipFile(StringIO.StringIO(response.body))
        self.assertEqual(sorted(zip_res.namelist()),
            sorted(['0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml',
             '0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.pdf']))

    def test_GET_nonexisting_member(self):
        import zipfile
        import StringIO
        attempt = self._makeOne()

        response = self.testapp.get(
            '/api/v1/files/%s/target.zip/?file=nonexisting.xml' % attempt.id,
            status=400)

    def test_GET_full_package(self):
        import zipfile
        import StringIO
        attempt = self._makeOne()

        response = self.testapp.get(
            '/api/v1/files/%s/target.zip/?full=true' % attempt.id,
            status=200)

        zip_res = zipfile.ZipFile(StringIO.StringIO(response.body))
        # the zip contains 2 files and 1 directory.
        self.assertEqual(len(zip_res.namelist()), 3)


@unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
class HealthStatusTests(unittest.TestCase):
    """
    It is not necessary to test the status and description contents as long as
    they are tested in `test_health.py`.
    """
    def setUp(self):
        self.config = testing.setUp()

        app = httpd.main(ConfigStub(), global_engine)
        self.testapp = TestApp(app)

    def tearDown(self):
        testing.tearDown()

    def test_DBConnection(self):
        response = self.testapp.get('/status/')
        results = response.json['results']
        self.assertTrue('DBConnection' in results)
        self.assertTrue('status' in results['DBConnection'])
        self.assertTrue('description' in results['DBConnection'])

    def test_NotificationsOption(self):
        response = self.testapp.get('/status/')
        results = response.json['results']
        self.assertTrue('NotificationsOption' in results)
        self.assertTrue('status' in results['NotificationsOption'])
        self.assertTrue('description' in results['NotificationsOption'])

