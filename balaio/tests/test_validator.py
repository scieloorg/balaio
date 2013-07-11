# coding: utf-8
import unittest
import mocker

from balaio import validator

#
# Stubs are test doubles to be used when the test does not aim
# to check inner aspects of a collaboration.
#
class ScieloAPIClientStub(object):
    def __init__(self, *args, **kwargs):
        pass


class NotifierStub(object):
    def __init__(self, *args, **kwargs):
        pass

    def validation_event(self, *args, **kwargs):
        pass


#
# Module level constants
#
class ConstantsTests(unittest.TestCase):

    def test_STATUS_OK_value(self):
        self.assertEqual(validator.STATUS_OK, 'ok')

    def test_STATUS_WARNING_value(self):
        self.assertEqual(validator.STATUS_WARNING, 'warning')

    def test_STATUS_ERROR_value(self):
        self.assertEqual(validator.STATUS_ERROR, 'error')


#
# Pipes
#
class ValidationPipeTests(mocker.MockerTestCase):

    def test_scieloapi_arg_is_mandatory(self):
        self.assertRaises(ValueError,
                          lambda: validator.ValidationPipe([{'name': 'foo'}]))

    def test_scieloapi_isnt_called_during_initialization(self):
        mock_scieloapi = self.mocker.mock()
        self.mocker.replay()

        vpipe = validator.ValidationPipe([{'name': 'foo'}], scieloapi=mock_scieloapi)
        self.assertIsInstance(vpipe, validator.ValidationPipe)

    def test_notifier_is_called_during_initialization(self):
        mock_notifier = self.mocker.mock()
        mock_scieloapi = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        self.mocker.replay()

        vpipe = validator.ValidationPipe([{'name': 'foo'}],
            scieloapi=mock_scieloapi, notifier_dep=mock_notifier)

        self.assertIsInstance(vpipe, validator.ValidationPipe)

    def test_transform_calls_validate_stage_notifier(self):
        """
        Asserts that methods expected to be defined by the subclasses are being called.
        """
        mock_self = self.mocker.mock(validator.ValidationPipe)

        mock_self.validate('pkg_analyzer')
        self.mocker.result(['ok', 'foo'])

        mock_self._stage_
        self.mocker.result('bar')

        mock_self._notifier.validation_event(mocker.ANY)
        self.mocker.result(None)

        self.mocker.replay()

        self.assertEqual(
            validator.ValidationPipe.transform(mock_self, ['attempt', 'pkg_analyzer']),
            ['attempt', 'pkg_analyzer'])

    def test_validate_raises_NotImplementedError(self):
        vpipe = validator.ValidationPipe([{'name': 'foo'}],
            scieloapi=ScieloAPIClientStub(), notifier_dep=NotifierStub)

        self.assertRaises(NotImplementedError, lambda: vpipe.validate('foo'))

