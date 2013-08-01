import unittest

import mocker

from balaio import vpipes
from balaio.tests.doubles import *


class PipelineTests(mocker.MockerTestCase):

    def test_configure_wraps_pipe_instantiation(self):
        class ConfigPipe(vpipes.ConfigMixin, vpipes.Pipe):
            __requires__ = ['_scieloapi', '_notifier']
            def transform(self, data):
                return data

        ppl = vpipes.Pipeline(ConfigPipe)
        ppl.configure(_scieloapi=ScieloAPIClientStub(),
                      _notifier=NotifierStub())

        self.assertNotEqual(ConfigPipe, ppl._pipes[0])

        for res in ppl.run([{'foo': 'bar'}]):
            self.assertEqual({'foo': 'bar'}, res)


class ValidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        from balaio import vpipes
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())

        vpipe = vpipes.ValidationPipe(data)
        vpipe.configure(_scieloapi=_scieloapi,
                        _notifier=_notifier,
                        _sapi_tools=_sapi_tools)
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

