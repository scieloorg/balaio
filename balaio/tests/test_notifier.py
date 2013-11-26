import unittest

import mocker

from balaio.notifier import Notifier
from balaio import models
from . import doubles, modelfactories
from .utils import db_bootstrap


global_engine = None


def setUpModule():
    """
    Initialize the database.
    """
    global global_engine
    global_engine = db_bootstrap()


class NotifierTests(mocker.MockerTestCase):

    def _makeOne(self, **kwargs):
        checkpoint = kwargs.get('checkpoint', modelfactories.CheckpointFactory())
        scieloapi = kwargs.get('scieloapi', doubles.ScieloAPIClientStub())
        db_session = kwargs.get('db_session', doubles.SessionStub())

        return Notifier(checkpoint, scieloapi, db_session)

    def test_start_sends_notification_on_checkin_points(self):
        checkpoint = modelfactories.CheckpointFactory(point=models.Point.checkin)
        notifier = self._makeOne(checkpoint=checkpoint)

        mock_notifier = self.mocker.patch(notifier)
        mock_notifier._send_checkin_notification()
        self.mocker.result(None)
        self.mocker.replay()

        notifier.start()

    def test_start_doesnt_send_notification_otherwise(self):
        checkpoint = modelfactories.CheckpointFactory(point=models.Point.validation)
        notifier = self._makeOne(checkpoint=checkpoint)

        mock_notifier = self.mocker.patch(notifier)
        mock_notifier._send_checkin_notification()
        self.mocker.result(None)
        self.mocker.count(0,0)  # means the method is not called
        self.mocker.replay()

        notifier.start()

    def test_send_checkin_notification_payload(self):
        checkpoint = modelfactories.CheckpointFactory(point=models.Point.checkin)

        expected = {
             'articlepkg_ref': str(checkpoint.attempt.articlepkg.id),
             'attempt_ref': str(checkpoint.attempt.id),
             'article_title': checkpoint.attempt.articlepkg.article_title,
             'journal_title': checkpoint.attempt.articlepkg.journal_title,
             'issue_label': '##',
             'package_name': checkpoint.attempt.filepath,
             'uploaded_at': str(checkpoint.attempt.started_at),
        }

        mock_scieloapi = self.mocker.mock()
        mock_scieloapi.checkins.post(expected)
        self.mocker.result(None)
        self.mocker.replay()

        notifier = self._makeOne(checkpoint=checkpoint, scieloapi=mock_scieloapi)
        self.assertIsNone(notifier._send_checkin_notification())

    def test_send_notice_notification_on_checkin_points(self):
        checkpoint = modelfactories.CheckpointFactory(point=models.Point.checkin)
        notifier = self._makeOne(checkpoint=checkpoint)

        mock_notifier = self.mocker.patch(notifier)

        mock_notifier._send_checkin_notification()
        self.mocker.result(None)

        mock_notifier._send_notice_notification('foo', models.Status.ok, label='bar')
        self.mocker.result(None)

        self.mocker.replay()

        notifier.start()
        notifier.tell('foo', models.Status.ok, label='bar')

    def test_send_notice_notification_payload(self):
        checkpoint = modelfactories.CheckpointFactory(point=models.Point.validation)
        checkpoint.attempt.checkin_uri = '/api/v1/checkins/1/'

        expected = {
            'checkin': '/api/v1/checkins/1/',
            'stage': 'bar',
            'checkpoint': 'validation',
            'message': 'foo',
            'status': 'ok',
        }

        mock_scieloapi = self.mocker.mock()
        mock_scieloapi.notices.post(expected)
        self.mocker.result(None)
        self.mocker.replay()

        notifier = self._makeOne(checkpoint=checkpoint, scieloapi=mock_scieloapi)
        self.assertIsNone(notifier._send_notice_notification(
            'foo', models.Status.ok, label='bar'))

