import unittest

import mocker

from balaio import vpipes
from balaio.tests.doubles import *


class ValidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        from balaio import vpipes
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())

        vpipe = vpipes.ValidationPipe(scieloapi=_scieloapi,
                                      notifier=_notifier,
                                      sapi_tools=_sapi_tools)
        vpipe.feed(data)
        return vpipe

    def test_scieloapi_isnt_called_during_initialization(self):
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = self._makeOne([{'name': 'foo'}], _scieloapi=mock_scieloapi)
        self.assertIsInstance(vpipe, vpipes.ValidationPipe)

    def test_notifier_isnt_called_during_initialization(self):
        mock_notifier = self.mocker.mock()
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = self._makeOne([{'name': 'foo'}],
            _scieloapi=mock_scieloapi, _notifier=mock_notifier)

        self.assertIsInstance(vpipe, vpipes.ValidationPipe)

    def test_transform_calls_validate_stage_notifier(self):
        """
        Asserts that methods expected to be defined by the subclasses are being called.
        """
        mock_self = self.mocker.mock(vpipes.ValidationPipe)

        mock_self.validate(['attempt', 'pkg_analyzer', {}])
        self.mocker.result(['ok', 'foo'])

        mock_self._stage_
        self.mocker.result('bar')

        mock_self._notifier.validation_event(mocker.ANY)
        self.mocker.result(None)

        self.mocker.replay()

        self.assertEqual(
            vpipes.ValidationPipe.transform(mock_self, ['attempt', 'pkg_analyzer', {}]),
            ['attempt', 'pkg_analyzer', {}])

    def test_validate_raises_NotImplementedError(self):
        vpipe = self._makeOne([{'name': 'foo'}])
        self.assertRaises(NotImplementedError, lambda: vpipe.validate('foo'))

