# coding: utf-8
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree

import unittest
import mocker

from balaio import validator


class Patch(object):
    def __init__(self, target, patch):
        self.target = target
        self.patch = patch
        self._toggle()

    def _toggle(self):
        self.target, self.patch = self.patch, self.target

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self._toggle()


#
# Stubs are test doubles to be used when the test does not aim
# to check inner aspects of a collaboration.
#
class ScieloAPIClientStub(object):
    def __init__(self, *args, **kwargs):
        self.journals = EndpointStub()


class EndpointStub(object):

    def get(self, *args, **kwargs):
        return {}

    def filter(self, *args, **kwargs):
        return (_ for _ in range(5))

    def all(self, *args, **kwargs):
        return (_ for _ in range(5))


class NotifierStub(object):
    def __init__(self, *args, **kwargs):
        pass

    def validation_event(self, *args, **kwargs):
        pass


class PackageAnalyzerStub(object):
    def __init__(self, *args, **kwargs):
        """
        `_xml_string` needs to be patched.
        """
        self._xml_string = None

    @property
    def xml(self):
        etree = ElementTree()
        return etree.parse(StringIO(self._xml_string))


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


class PISSNValidationPipeTests(unittest.TestCase):
    def _makeOne(self, data):
        return validator.PISSNValidationPipe(data,
                                             scieloapi=ScieloAPIClientStub(),
                                             notifier_dep=NotifierStub)

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_missing_pissn_is_ok(self):
        expected = ['ok', '']
        data = "<root></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_one_valid_ISSN(self):
        expected = ['ok', '']
        data = "<root><issn pub-type='ppub'>0102-6720</issn></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_one_invalid_ISSN_raises_warning(self):
        """
        Invalid PISSN raises a waning instead of an error since
        it is not a blocking condition.
        """
        expected = ['warning', 'print ISSN is invalid']
        data = "<root><issn pub-type='ppub'>1234-1234</issn></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_two_valid_ISSN_eletronic_and_print(self):
        expected = ['ok', '']
        data = "<root><issn pub-type='ppub'>0100-879X</issn><issn pub-type='epub'>1414-431X</issn></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)


class EISSNValidationPipeTests(unittest.TestCase):
    def _makeOne(self, data):
        return validator.EISSNValidationPipe(data,
                                             scieloapi=ScieloAPIClientStub(),
                                             notifier_dep=NotifierStub)

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_one_valid_ISSN(self):
        expected = ['ok', '']
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_one_invalid_ISSN(self):
        expected = ['error', 'electronic ISSN is invalid']
        data = "<root><issn pub-type='epub'>1234-1234</issn></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_two_valid_ISSN_eletronic_and_print(self):
        expected = ['ok', '']
        data = "<root><issn pub-type='ppub'>0100-879X</issn><issn pub-type='epub'>1414-431X</issn></root>"

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

