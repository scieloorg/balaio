# coding: utf-8
import unittest
import mocker

from balaio.lib import models, utils
from balaio.lib.validations import journal
from balaio.tests.doubles import *


class JournalAbbreviatedTitleValidationTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        _normalize_data = kwargs.get('_normalize_data', utils.normalize_data)

        vpipe = journal.JournalAbbreviatedTitleValidationPipe(_notifier, _normalize_data)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_valid_abbreviated_title(self):
        expected = [models.Status.ok, u'Valid abbrev-journal-title: An. Acad. Bras. Ciênc.']
        xml = '''
            <front>
              <journal-meta>
                <journal-title-group>
                  <abbrev-journal-title abbrev-type="publisher"><![CDATA[An. Acad. Bras. Ciênc.]]></abbrev-journal-title>
                </journal-title-group>
              </journal-meta>
            </front>'''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'An. Acad. Bras. Ciênc.')
        self.mocker.result(u'AN. ACAD. BRAS. CIÊNC.')

        self.mocker.count(2)

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'short_title': u'An. Acad. Bras. Ciênc.'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_invalid_abbreviated_title(self):
        expected = [models.Status.error, u'Mismatched data: An. Academia Bras. Ciênc.. Expected: An. Acad. Bras. Ciênc.']
        xml = '''
            <front>
              <journal-meta>
                <journal-title-group>
                  <abbrev-journal-title abbrev-type="publisher"><![CDATA[An. Academia Bras. Ciênc.]]></abbrev-journal-title>
                </journal-title-group>
              </journal-meta>
            </front>'''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'An. Academia Bras. Ciênc.')
        self.mocker.result(u'AN. ACADEMIA. BRAS. CIÊNC.')

        mock_normalize_data(u'An. Acad. Bras. Ciênc.')
        self.mocker.result(u'AN. ACAD. BRAS. CIÊNC.')

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'short_title': u'An. Acad. Bras. Ciênc.'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_if_exists_abbreviated_title_tag_on_source(self):
        expected = [models.Status.error, 'Missing data: short_title, in scieloapi']
        xml = '''
            <front>
              <journal-meta>
                <journal-title-group>
                  <abbrev-journal-title abbrev-type="publisher"><![CDATA[An. Academia Bras. Ciênc.]]></abbrev-journal-title>
                </journal-title-group>
              </journal-meta>
            </front>'''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_if_exists_abbreviated_title_tag_on_xml(self):
        expected = [models.Status.error, 'Missing data: abbrev-journal-title']
        xml = '''
              <front>
                <journal-meta>
                  <journal-title-group></journal-title-group>
                </journal-meta>
              </front>
              '''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {'short_title': u'An. Acad. Bras. Ciênc.'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))


class PublisherNameValidationPipeTests(mocker.MockerTestCase):
    """
    docstring for PublisherNameValidationPipeTests
    """
    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        _normalize_data = kwargs.get('_normalize_data', utils.normalize_data)

        vpipe = journal.PublisherNameValidationPipe(_notifier, _normalize_data)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_publisher_name_matched(self):
        expected = [models.Status.ok, 'Valid publisher name: publicador                  da revista brasileira de ....']
        xml = '<root><journal-meta><publisher><publisher-name>publicador                  da revista brasileira de ....</publisher-name></publisher></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'publicador                  da revista brasileira de ....')
        self.mocker.result(u'PUBLICADOR DA REVISTA BRASILEIRA DE ....')

        mock_normalize_data(u'publicador da revista brasileira de ....')
        self.mocker.result(u'PUBLICADOR DA REVISTA BRASILEIRA DE ....')

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'publisher_name': 'publicador da revista brasileira de ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        vpipe._normalize_data = mock_normalize_data
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_unmatched(self):
        expected = [models.Status.error, 'Mismatched data: publicador abcdefgh. Expected: publicador da revista brasileira de ....']
        xml = '<root><journal-meta><publisher><publisher-name>publicador abcdefgh</publisher-name></publisher></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'publicador abcdefgh')
        self.mocker.result(u'PUBLICADOR ABCDEFGH')

        mock_normalize_data(u'publicador da revista brasileira de ....')
        self.mocker.result(u'PUBLICADOR DA REVISTA BRASILEIRA DE ....')

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'publisher_name': 'publicador da revista brasileira de ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        vpipe._normalize_data = mock_normalize_data
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_is_missing_in_journal(self):
        expected = [models.Status.error, 'Missing data: publisher name, in scieloapi']
        xml = '<root><journal-meta><publisher><publisher-name>publicador abcdefgh</publisher-name></publisher></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {}}
        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_is_missing_in_article(self):
        expected = [models.Status.error, 'Missing data: publisher name']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {'publisher_name': 'publicador da revista brasileira de ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))


class NLMJournalTitleValidationPipeTests(mocker.MockerTestCase):
    """
    Tests of NLMJournalTitleValidationPipe
    """
    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        _normalize_data = kwargs.get('_normalize_data', utils.normalize_data)

        vpipe = journal.NLMJournalTitleValidationPipe(_notifier, _normalize_data)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_nlm_journal_title_matched(self):
        expected = [models.Status.ok, 'Valid NLM journal title: NLM Journal title']
        xml = '<root><journal-meta><journal-id journal-id-type="nlm-ta">NLM Journal title</journal-id></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'NLM Journal title')
        self.mocker.result(u'NLM JOURNAL TITLE')

        self.mocker.count(2)

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'medline_title': 'NLM Journal title'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_nlm_journal_title_unmatched(self):
        expected = [models.Status.error, 'Mismatched data: ANY Journal Title. Expected: NLM Journal Title ....']
        xml = '<root><journal-meta><journal-id journal-id-type="nlm-ta">ANY Journal Title</journal-id></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'ANY Journal Title')
        self.mocker.result(u'ANY JOURNAL TITLE')

        mock_normalize_data(u'NLM Journal Title ....')
        self.mocker.result(u'NLM JOURNAL TITLE ....')

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'medline_title': 'NLM Journal Title ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_nlm_journal_title_is_missing_in_journal(self):
        expected = [models.Status.error, 'Mismatched data: ANY Journal Title. Expected: ']
        xml = '<root><journal-meta><journal-id journal-id-type="nlm-ta">ANY Journal Title</journal-id></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_nlm_journal_title_is_missing_in_article(self):
        expected = [models.Status.error, 'Mismatched data: . Expected: NLM Journal Title ....']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {'medline_title': 'NLM Journal Title ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

