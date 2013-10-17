import unittest

import mocker

from balaio import vpipes
from balaio.tests.doubles import *
from balaio import models

class ValidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        from balaio import vpipes
        _notifier = kwargs.get('_notifier', lambda args: NotifierStub)
        
        vpipe = vpipes.ValidationPipe(notifier=_notifier)
        vpipe.feed(data)
        return vpipe

    def test_notifier_isnt_called_during_initialization(self):
        mock_notifier = self.mocker.mock()
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = self._makeOne([{'name': 'foo'}], _notifier=mock_notifier)

        self.assertIsInstance(vpipe, vpipes.ValidationPipe)

    def test_transform_calls_validate_stage_notifier(self):
        """
        Asserts that methods expected to be defined by the subclasses are being called.
        """
        vpipes.ValidationPipe._notifier = NotifierStub()
        mock_self = self.mocker.mock(vpipes.ValidationPipe)

        item = [AttemptStub(), ArticlePkgStub(), {}]

        mock_self.validate(item)
        self.mocker.result([models.Status.ok, 'foo'])

        mock_self._stage_
        self.mocker.result('bar')

        #mock_self._notifier.validation_event(mocker.ANY)
        # self.mocker.result(None)
        mock_self._notifier(item[0])
        self.mocker.result(NotifierStub())

        self.mocker.replay()

        self.assertEqual(
            vpipes.ValidationPipe.transform(mock_self, item),
            item)

    def test_validate_raises_NotImplementedError(self):
        vpipe = self._makeOne([{'name': 'foo'}])
        self.assertRaises(NotImplementedError, lambda: vpipe.validate('foo'))

