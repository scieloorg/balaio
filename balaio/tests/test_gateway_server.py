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


class ValidationAPITest(unittest.TestCase):

    def setUp(self):
        self.req = testing.DummyRequest()
        self.req.registry.settings = {'http_server': {'version': 'v1'}}
        self.req.db = ObjectStub()
        self.req.db.query = QueryStub
        self.req.db.query.model = ValidationStub

    def test_view_validations(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': [ValidationStub().to_dict(), ValidationStub().to_dict()]}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = True

        self.assertEqual(
            gateway_server.list_validation(self.req),
            expected)

    def test_view_validations_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': []}

        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = False

        self.assertEqual(
            gateway_server.list_validation(self.req),
            expected)

    def test_view_validation(self):
        expected = ValidationStub().to_dict()

        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}

        self.assertEqual(
            gateway_server.validation(self.req),
            expected)

    def test_view_validation_no_result(self):
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            gateway_server.validation(self.req),
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