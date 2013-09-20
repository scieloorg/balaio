import unittest

from pyramid import testing
from balaio import gateway_server
from balaio.tests.doubles import *
from pyramid.httpexceptions import HTTPNotFound


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

    def test_new_ticket_no_comments(self):
        expected = {
            "articlepkg_id": 3,
            "id": 5,
            "finished_at": None,
            "is_open": True,
            "resource_uri": "/api/v1/tickets/1/",
            "started_at": "2012-07-24T21:53:23.909404",
            "comments": [],
        }
        self.req.params = {'submit': True}
        self.req.POST = {
            'articlepkg_id': 3,
        }

        mock_model = self.mocker.mock()
        mock_model.Ticket()
        self.mocker.result(TicketStub())

        self.assertEqual(
            gateway_server.new_ticket(self.req),
            expected
        )

        comments = relationship('Comment', backref='ticket')

