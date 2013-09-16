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

        gateway_server.config = self.mocker.mock()
        gateway_server.config.get('http_server', 'limit')
        self.mocker.result(20)

        mocked_response = self.mocker.mock()
        mocked_response.offset(0)
        self.mocker.result([AttemptStub(), AttemptStub()])

        mocked_query = self.mocker.mock()
        mocked_query.limit(20)
        self.mocker.result(mocked_response)

        mocked_query.scalar()
        self.mocker.result(200)

        mocked_db = self.mocker.mock()
        mocked_db.query(mocker.ANY)
        self.mocker.count(2)
        self.mocker.result(mocked_query)

        mocked_request = self.mocker.mock()

        mocked_request.db
        self.mocker.result(mocked_db)
        self.mocker.count(2)

        mocked_request.params.get('limit', 20)
        self.mocker.result(20)

        mocked_request.params.get('offset', 0)
        self.mocker.result(0)

        gateway_server.func = self.mocker.mock()
        gateway_server.func.count(models.Attempt.id)
        self.mocker.result(mocked_query)

        self.mocker.replay()

        self.assertEqual(
            gateway_server.attempts(mocked_request),
            expected)

    def test_view_attempts_no_item(self):
        expected = {'limit': 20,
                    'offset': 0,
                    'total': 200,
                    'objects': []}

        gateway_server.config = self.mocker.mock()
        gateway_server.config.get('http_server', 'limit')
        self.mocker.result(20)

        mocked_response = self.mocker.mock()
        mocked_response.offset(0)
        self.mocker.result([])

        mocked_query = self.mocker.mock()
        mocked_query.limit(20)
        self.mocker.result(mocked_response)

        mocked_query.scalar()
        self.mocker.result(200)

        mocked_db = self.mocker.mock()
        mocked_db.query(mocker.ANY)
        self.mocker.count(2)
        self.mocker.result(mocked_query)

        mocked_request = self.mocker.mock()

        mocked_request.db
        self.mocker.result(mocked_db)
        self.mocker.count(2)

        mocked_request.params.get('limit', 20)
        self.mocker.result(20)

        mocked_request.params.get('offset', 0)
        self.mocker.result(0)

        gateway_server.func = self.mocker.mock()
        gateway_server.func.count(models.Attempt.id)
        self.mocker.result(mocked_query)

        self.mocker.replay()

        self.assertEqual(
            gateway_server.attempts(mocked_request),
            expected)

    def test_view_attempt(self):
        #attempt = request.db.query(models.Attempt).filter_by(id=request.matchdict['id']).one()
        expected = AttemptStub().to_dict()

        mocked_response = self.mocker.mock()
        mocked_response.one()
        self.mocker.result(AttemptStub())

        mocked_query = self.mocker.mock()
        mocked_query.filter_by(id=1)
        self.mocker.result(mocked_response)

        mocked_db = self.mocker.mock()
        mocked_db.query(models.Attempt)
        self.mocker.result(mocked_query)

        mocked_request = self.mocker.mock()
        mocked_request.matchdict['id']
        self.mocker.result(1)

        mocked_request.db
        self.mocker.result(mocked_db)

        self.mocker.replay()

        self.assertEqual(
            gateway_server.attempt(mocked_request),
            expected)

    def test_view_attempt_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound

        mocked_response = self.mocker.mock()
        mocked_response.one()
        self.mocker.result(None)

        mocked_query = self.mocker.mock()
        mocked_query.filter_by(id=1)
        self.mocker.result(mocked_response)

        mocked_db = self.mocker.mock()
        mocked_db.query(models.Attempt)
        self.mocker.result(mocked_query)

        mocked_request = self.mocker.mock()
        mocked_request.matchdict['id']
        self.mocker.result(1)

        mocked_request.db
        self.mocker.result(mocked_db)

        self.mocker.replay()

        self.assertIsInstance(
            gateway_server.attempt(mocked_request),
            HTTPNotFound)
