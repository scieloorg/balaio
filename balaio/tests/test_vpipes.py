import unittest

import mocker

from balaio import vpipes
from balaio.tests.doubles import *


class PipelineTests(mocker.MockerTestCase):

    def test_configure_wraps_pipe_instantiation(self):

        ppl = vpipes.Pipeline(PipeStub)
        ppl.configure(ScieloAPIClientStub(),
                      NotifierStub())

        self.assertNotEqual(PipeStub, ppl._pipes[0])

        for res in ppl.run([{'foo': 'bar'}]):
            self.assertEqual({'foo': 'bar'}, res)


class ValidationPipeTests(mocker.MockerTestCase):

    def test_scieloapi_arg_is_mandatory(self):
        self.assertRaises(ValueError,
                          lambda: vpipes.ValidationPipe([{'name': 'foo'}]))

    def test_scieloapi_isnt_called_during_initialization(self):
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = vpipes.ValidationPipe([{'name': 'foo'}],
                                      scieloapi=mock_scieloapi,
                                      notifier_dep=NotifierStub())
        self.assertIsInstance(vpipe, vpipes.ValidationPipe)

    def test_notifier_isnt_called_during_initialization(self):
        mock_notifier = self.mocker.mock()
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = vpipes.ValidationPipe([{'name': 'foo'}],
            scieloapi=mock_scieloapi, notifier_dep=mock_notifier)

        self.assertIsInstance(vpipe, vpipes.ValidationPipe)

    def test_transform_calls_validate_stage_notifier(self):
        """
        Asserts that methods expected to be defined by the subclasses are being called.
        """
        mock_self = self.mocker.mock(vpipes.ValidationPipe)

        mock_self.validate('pkg_analyzer')
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
        vpipe = vpipes.ValidationPipe([{'name': 'foo'}],
            scieloapi=ScieloAPIClientStub(), notifier_dep=NotifierStub)

        self.assertRaises(NotImplementedError, lambda: vpipe.validate('foo'))
