#coding: utf-8
import sys, os
import unittest
import transaction
from webtest import TestApp

from pyramid import testing
from balaio import gateway_server
from balaio.tests.doubles import *
from sqlalchemy import create_engine
from balaio.gateway_server import main
from pyramid.httpexceptions import HTTPNotFound

from balaio import models

sys.path.append(os.path.dirname(__file__) + '/../')


def _initTestingDB(model):

    engine = create_engine('sqlite://')
    models.Base.metadata.create_all(engine)

    models.Session.configure(bind=engine)

    with transaction.manager:
        models.Session.add(model)

    return models.Session


class PackageFunctionalAPITest(unittest.TestCase):

    def _makeOne(self):
        article = models.ArticlePkg(id=1,
                    journal_title='Associa... Brasileira',
                    article_title='Construction of a recombinant adenovirus...',
                    journal_pissn='0100-879X',
                    journal_eissn='0100-879X',
                    issue_year=1995,
                    issue_volume='67',
                    issue_number='8',
                    issue_suppl_volume=None,
                    issue_suppl_number=None)

        return article

    def setUp(self):
        self.session = _initTestingDB(self._makeOne())
        self.config = testing.setUp()

        app, config = main()
        self.testapp = TestApp(app)

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    def test_root(self):
        resp = self.testapp.get('/', status=200)
        self.assertTrue('Gateway version v1' in resp.body)

    def test_GET_to_available_resource(self):
        self.testapp.get('/api/v1/packages/', status=200)

    def test_GET_to_unavailable_resource(self):
        self.testapp.get('/api/v1/pkg/', status=404)

    def test_GET_to_one_package(self):
        res = self.testapp.get('/api/v1/packages/1/')
        self.assertEqual(res.body, u'{"article_title": "Construction of a recombinant adenovirus...", "issue_year": 1995, "journal_title": "Associa... Brasileira", "journal_pissn": "0100-879X", "journal_eissn": "0100-879X", "issue_suppl_number": null, "attempts": [], "issue_suppl_volume": null, "issue_volume": "67", "resource_uri": "/api/v1/packages/1/1", "id": 1, "issue_number": "8"}')

    def test_GET_to_packages(self):
        res = self.testapp.get('/api/v1/packages/')
        self.assertEqual(res.body, u'{"meta": {"total_count": 1, "limit": "20", "offset": 0}, "objects": [{"article_title": "Construction of a recombinant adenovirus...", "issue_year": 1995, "journal_title": "Associa... Brasileira", "journal_pissn": "0100-879X", "journal_eissn": "0100-879X", "issue_suppl_number": null, "attempts": [], "issue_suppl_volume": null, "issue_volume": "67", "resource_uri": "/api/v1/packages/1", "id": 1, "issue_number": "8"}]}')


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
                    'total': 200,
                    'objects': [AttemptStub().to_dict(), AttemptStub().to_dict()]}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = True

        self.assertEqual(
            gateway_server.attempts(self.req),
            expected)

    def test_view_attempts_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': []}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = False

        self.assertEqual(
            gateway_server.attempts(self.req),
            expected)

    def test_view_attempt(self):
        expected = AttemptStub().to_dict()

        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}
        self.assertEqual(
            gateway_server.attempt(self.req),
            expected)

    def test_view_attempt_no_result(self):
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            gateway_server.attempt(self.req),
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
                    'total': 200,
                    'objects': [ArticlePkgStub().to_dict(), ArticlePkgStub().to_dict()]}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = True

        self.assertEqual(
            gateway_server.list_package(self.req),
            expected)

    def test_view_packages_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': []}
        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = False

        self.assertEqual(
            gateway_server.list_package(self.req),
            expected)

    def test_view_package(self):
        expected = ArticlePkgStub().to_dict()

        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}

        self.assertEqual(
            gateway_server.package(self.req),
            expected)

    def test_view_package_no_result(self):
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            gateway_server.attempt(self.req),
            HTTPNotFound
        )


class TicketAPITest(unittest.TestCase):

    def setUp(self):
        self.req = testing.DummyRequest()
        self.req.registry.settings = {'http_server': {'version': 'v1'}}
        self.req.db = ObjectStub()
        self.req.db.query = QueryStub
        self.req.db.query.model = TicketStub

    def test_view_tickets(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': [TicketStub().to_dict(), TicketStub().to_dict()]}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = True

        self.assertEqual(
            gateway_server.list_ticket(self.req),
            expected)

    def test_view_tickets_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': []}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = False

        self.assertEqual(
            gateway_server.list_ticket(self.req),
            expected)

    def test_view_ticket(self):
        expected = TicketStub().to_dict()

        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}

        self.assertEqual(
            gateway_server.ticket(self.req),
            expected)

    def test_view_ticket_no_result(self):
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            gateway_server.ticket(self.req),
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
            gateway_server.get_query_filters(model, request_params)
            )
