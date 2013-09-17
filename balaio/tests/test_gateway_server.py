import unittest

import mocker

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.orm import sessionmaker

from balaio import gateway_server
from balaio.tests.doubles import *
from balaio import models


class AttemptsAPITest(mocker.MockerTestCase):

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
        self.setUp()
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
        self.setUp()
        self.req.params = {'limit': 20, 'offset': 0}
        self.req.db.query.found = False

        self.assertEqual(
            gateway_server.attempts(self.req),
            expected)

    def test_view_attempt(self):
        expected = AttemptStub().to_dict()

        self.setUp()
        self.req.db.query.found = True
        self.req.matchdict = {'id': 1}
        self.assertEqual(
            gateway_server.attempt(self.req),
            expected)

    def test_view_attempt_no_result(self):
        self.setUp()
        self.req.db.query.found = False
        self.req.matchdict = {'id': 1}

        self.assertIsInstance(
            gateway_server.attempt(self.req),
            HTTPNotFound
        )
