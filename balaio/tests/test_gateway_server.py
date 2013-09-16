import unittest

import mocker

from pyramid import testing
from sqlalchemy.orm import sessionmaker

from balaio import gateway_server
from balaio.tests.doubles import *
from balaio import models


class AttemptsAPITest(mocker.MockerTestCase):

    def test_view_attempts(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': [AttemptStub().to_dict(), AttemptStub().to_dict()]}

        #request = RequestStub()
        req = testing.DummyRequest()
        req.registry.settings = {'http_server': {'version': 'v1'}}
        req.params = {'limit': 20, 'offset': 0}
        req.db = ObjectStub()
        req.db.query = QueryStub
        req.db.query.model = AttemptStub
        req.db.query.found = True

        self.assertEqual(
            gateway_server.attempts(req),
            expected)

    def test_view_attempts_no_result(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': []}

        #request = RequestStub()
        req = testing.DummyRequest()
        req.registry.settings = {'http_server': {'version': 'v1'}}
        req.params = {'limit': 20, 'offset': 0}
        req.db = ObjectStub()
        req.db.query = QueryStub
        req.db.query.model = AttemptStub
        req.db.query.found = False

        self.assertEqual(
            gateway_server.attempts(req),
            expected)

    # def test_view_attempts(self):
    #     expected = {'limit': 20,
    #                 'offset': 0,
    #                 'total': 200,
    #                 'objects': [AttemptStub().to_dict(), AttemptStub().to_dict()]}

    #     request = RequestStub(AttemptStub)
    #     self.assertEqual(
    #         gateway_server.attempts(request),
    #         expected)

    # def test_view_attempts_no_result(self):
    #     expected = {'limit': 20,
    #                 'offset': 0,
    #                 'total': 200,
    #                 'objects': []}

    #     request = RequestStub(None)
    #     self.assertEqual(
    #         gateway_server.attempts(request),
    #         expected)

