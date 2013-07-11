# coding: utf-8
import unittest
import mocker

from balaio import validator


class ConstantsTests(unittest.TestCase):

    def test_STATUS_OK_value(self):
        self.assertEqual(validator.STATUS_OK, 'ok')

    def test_STATUS_WARNING_value(self):
        self.assertEqual(validator.STATUS_WARNING, 'warning')

    def test_STATUS_ERROR_value(self):
        self.assertEqual(validator.STATUS_ERROR, 'error')


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
        mock_self = self.mocker.nospec()

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

