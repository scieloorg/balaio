# coding: utf-8
import unittest
import mocker

from balaio import validator
from balaio.tests.doubles import *


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
class SetupPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        from balaio import utils
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)
        _issn_validator = kwargs.get('_issn_validator', utils.is_valid_issn)

        vpipe = validator.SetupPipe(data)
        vpipe.configure(_scieloapi=_scieloapi,
                        _notifier=_notifier,
                        _sapi_tools=_sapi_tools,
                        _pkg_analyzer=_pkg_analyzer,
                        _issn_validator=_issn_validator)
        return vpipe

    def test_transform_returns_right_datastructure(self):
        """
        The right datastructure is a tuple in the form:
        (<models.Attempt>, <checkin.PackageAnalyzer>, <dict>)
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapi = ScieloAPIClientStub()
        scieloapi.journals.filter = lambda print_issn=None, eletronic_issn=None, limit=None: [{}]

        vpipe = self._makeOne(data, _scieloapi=scieloapi)

        result = vpipe.transform(AttemptStub())

        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], AttemptStub)
        self.assertIsInstance(result[1], PackageAnalyzerStub)
        # index 2 is the return data from scieloapi.journals.filter
        # so, testing its type actualy means nothing.
        self.assertEqual(len(result), 3)

    def test_fetch_journal_data_with_valid_criteria(self):
        """
        Valid criteria means a valid querystring param.
        See a list at http://ref.scielo.org/nssk38

        The behaviour defined by the Restful API is to
        ignore the query for invalid criteria, and so
        do we.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"
        scieloapi = ScieloAPIClientStub()
        scieloapi.journals.filter = lambda **kwargs: [{'foo': 'bar'}]

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        self.assertEqual(vpipe._fetch_journal_data({'print_issn': '1234-1234'}),
                         {'foo': 'bar'})

    def test_fetch_journal_data_with_unknown_issn_raises_ValueError(self):
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"
        scieloapi = ScieloAPIClientStub()
        scieloapi.journals.filter = lambda **kwargs: []

        sapi_tools = get_ScieloAPIToolbeltStubModule()
        def _get_one(dataset):
            raise ValueError()
        sapi_tools.get_one = _get_one

        vpipe = self._makeOne(data, _scieloapi=scieloapi, _sapi_tools=sapi_tools)
        self.assertRaises(ValueError,
                          lambda: vpipe._fetch_journal_data({'print_issn': '1234-1234'}))

    def test_transform_grants_valid_issn_before_fetching(self):
        stub_attempt = AttemptStub()
        stub_attempt.articlepkg.journal_pissn = '0100-879X'
        stub_attempt.articlepkg.journal_eissn = None

        mock_issn_validator = self.mocker.mock()
        mock_fetch_journal_data = self.mocker.mock()

        with self.mocker.order():
            mock_issn_validator('0100-879X')
            self.mocker.result(True)

            mock_fetch_journal_data({'print_issn': '0100-879X'})
            self.mocker.result({'foo': 'bar'})

            self.mocker.replay()

        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        vpipe = self._makeOne(data)
        vpipe._issn_validator = mock_issn_validator
        vpipe._fetch_journal_data = mock_fetch_journal_data
        result = vpipe.transform(stub_attempt)


class PublisherNameValidationPipeTests(mocker.MockerTestCase):
    """
    docstring for PublisherNameValidationPipeTests
    """
    def _makeOne(self, data, **kwargs):
        from balaio import utils
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)
        #_issn_validator = kwargs.get('_issn_validator', utils.is_valid_issn)

        vpipe = validator.PublisherNameValidationPipe(data)
        vpipe.configure(_scieloapi=_scieloapi,
                        _notifier=_notifier,
                        _sapi_tools=_sapi_tools,
                        _pkg_analyzer=_pkg_analyzer)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_publisher_name_matched(self):
        expected = [validator.STATUS_OK, '']
        xml = '<root><publisher-name>publicador                  da revista brasileira de ....</publisher-name></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_data = {'publisher_name': 'publicador da revista brasileira de ....'}

        data = (stub_attempt, stub_package_analyzer, journal_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_unmatched(self):
        expected = [validator.STATUS_ERROR, 'publicador da revista brasileira de .... [journal]\npublicador abcdefgh [article]']
        xml = '<root><publisher-name>publicador abcdefgh</publisher-name></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_data = {'publisher_name': 'publicador da revista brasileira de ....'}

        data = (stub_attempt, stub_package_analyzer, journal_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_is_missing_in_journal(self):
        expected = [validator.STATUS_ERROR, 'Missing publisher_name in journal']
        xml = '<root><publisher-name>publicador abcdefgh</publisher-name></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_data = {}

        data = (stub_attempt, stub_package_analyzer, journal_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_is_missing_in_article(self):
        expected = [validator.STATUS_ERROR, 'Missing publisher-name in article']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_data = {'publisher_name': 'publicador da revista brasileira de ....'}

        data = (stub_attempt, stub_package_analyzer, journal_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))
