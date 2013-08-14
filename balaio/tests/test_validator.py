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
        scieloapi.issues.filter = lambda journal__print_issn=None, journal__eletronic_issn=None, journal=None, volume=None, number=None, suppl_volume=None, suppl_number=None, limit=None: [{}]

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

    def test_fetch_journal_issue_data_with_valid_criteria(self):
        """
        Valid criteria means a valid querystring param.
        See a list at http://ref.scielo.org/nssk38

        The behaviour defined by the Restful API is to
        ignore the query for invalid criteria, and so
        do we.
        """
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"
        scieloapi = ScieloAPIClientStub()
        scieloapi.issues.filter = lambda **kwargs: [{'foo': 'bar'}]

        vpipe = self._makeOne(data, _scieloapi=scieloapi)
        self.assertEqual(vpipe._fetch_journal_and_issue_data({'journal__print_issn': '0100-879X', 'volume': '30', 'number': '4'}),
                         {'foo': 'bar'})

    def test_transform_grants_valid_issn_before_fetching(self):
        stub_attempt = AttemptStub()
        stub_attempt.articlepkg.journal_pissn = '0100-879X'
        stub_attempt.articlepkg.journal_eissn = None
        stub_attempt.articlepkg.issue_volume = '30'
        stub_attempt.articlepkg.issue_number = '4'

        mock_issn_validator = self.mocker.mock()
        #mock_fetch_journal_data = self.mocker.mock()
        mock_fetch_journal_and_issue_data = self.mocker.mock()

        with self.mocker.order():
            mock_issn_validator('0100-879X')
            self.mocker.result(True)

            #mock_fetch_journal_data({'print_issn': '0100-879X'})
            #self.mocker.result({'foo': 'bar', 'resource_uri': '/api/...'})

            mock_fetch_journal_and_issue_data({'journal__print_issn': '0100-879X', 'volume': '30', 'number': '4'})
            self.mocker.result({'foo': 'bar'})

            self.mocker.replay()

        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        vpipe = self._makeOne(data)
        vpipe._issn_validator = mock_issn_validator
        #vpipe._fetch_journal_data = mock_fetch_journal_data
        vpipe._fetch_journal_and_issue_data = mock_fetch_journal_and_issue_data
        result = vpipe.transform(stub_attempt)


class JournalReferenceTypeValidationPipeTests(unittest.TestCase):

    def _makeOne(self, data, **kwargs):
        vpipe = validator.JournalReferenceTypeValidationPipe(data)

        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)
        _notifier = kwargs.get('_notifier', NotifierStub())

        vpipe.configure(_pkg_analyzer=_pkg_analyzer,
                        _notifier=_notifier)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_valid_reference_list(self):
        expected = [validator.STATUS_OK, '']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <person-group person-group-type="author">
                      <name>
                        <surname><![CDATA[Winkler]]></surname>
                        <given-names><![CDATA[JD]]></given-names>
                      </name>
                      <name>
                        <surname><![CDATA[Sánchez-Villagra]]></surname>
                        <given-names><![CDATA[MR]]></given-names>
                      </name>
                    </person-group>
                    <article-title xml:lang="en"><![CDATA[A nesting site and egg morphology of a Miocene turtle from Urumaco, Venezuela: evidence of marine adaptations in Pelomedusoides]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <year>2013</year>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_valid_without_reference_list(self):
        expected = [validator.STATUS_WARNING, 'this xml does not have reference list']
        data = '''
            <root>
              <journal-meta>
                <journal-id>0001-3765</journal-id>
                <journal-title><![CDATA[Anais da Academia Brasileira de Ciências]]></journal-title>
                <abbrev-journal-title><![CDATA[An. Acad. Bras. Ciênc.]]></abbrev-journal-title>
                <issn>0001-3765</issn>
                <publisher>
                  <publisher-name><![CDATA[Academia Brasileira de Ciências]]></publisher-name>
                </publisher>
              </journal-meta>
              <ref-list></ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_invalid_content_on_reference_list(self):
        expected = [validator.STATUS_ERROR, 'missing content on reference tags: source, article-title or year']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <person-group person-group-type="author">
                      <name>
                        <surname><![CDATA[Winkler]]></surname>
                        <given-names><![CDATA[JD]]></given-names>
                      </name>
                      <name>
                        <surname><![CDATA[Sánchez-Villagra]]></surname>
                        <given-names><![CDATA[MR]]></given-names>
                      </name>
                    </person-group>
                    <article-title xml:lang="en"><![CDATA[A nesting site and egg morphology of a Miocene turtle from Urumaco, Venezuela: evidence of marine adaptations in Pelomedusoides]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <year></year>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_reference_list_missing_any_tag(self):
        expected = [validator.STATUS_ERROR, 'missing some tag in reference list']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <person-group person-group-type="author">
                      <name>
                        <surname><![CDATA[Winkler]]></surname>
                        <given-names><![CDATA[JD]]></given-names>
                      </name>
                      <name>
                        <surname><![CDATA[Sánchez-Villagra]]></surname>
                        <given-names><![CDATA[MR]]></given-names>
                      </name>
                    </person-group>
                    <source><![CDATA[Palaeontology]]></source>
                    <year>2013</year>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)


class JournalAbbreviatedTitleValidationTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        vpipe = validator.JournalAbbreviatedTitleValidationPipe(data)

        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)
        _notifier = kwargs.get('_notifier', NotifierStub())

        vpipe.configure(_pkg_analyzer=_pkg_analyzer,
                        _notifier=_notifier,
                        _scieloapi=_scieloapi)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_valid_abbreviated_title(self):
        expected = [validator.STATUS_OK, '']
        xml = '''
            <front><journal-meta><abbrev-journal-title abbrev-type="publisher"><![CDATA[An. Acad. Bras. Ciênc.]]></abbrev-journal-title></journal-meta></front>'''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'An. Acad. Bras. Ciênc.')
        self.mocker.result(u'AN. ACAD. BRAS. CIÊNC.')

        self.mocker.count(2)

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'short_title': u'An. Acad. Bras. Ciênc.'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_invalid_abbreviated_title(self):
        expected = [validator.STATUS_ERROR, 'the abbreviated title in xml is defferent from the abbreviated title in the source']
        xml = '''
            <front><journal-meta><abbrev-journal-title abbrev-type="publisher"><![CDATA[An. Academia Bras. Ciênc.]]></abbrev-journal-title></journal-meta></front>'''

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

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_if_exists_abbreviated_title_tag_on_source(self):
        expected = [validator.STATUS_ERROR, 'missing abbreviated title in source']
        xml = '''
            <front><journal-meta><abbrev-journal-title abbrev-type="publisher"><![CDATA[An. Academia Bras. Ciênc.]]></abbrev-journal-title></journal-meta></front>'''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {}}
        

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_if_exists_abbreviated_title_tag_on_xml(self):
        expected = [validator.STATUS_ERROR, 'missing abbreviated title in xml']
        xml = '''
            <front><journal-meta></journal-meta></front>'''

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {'short_title': u'An. Acad. Bras. Ciênc.'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))


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

        mock_normalize_data = self.mocker.mock()
        mock_normalize_data(u'publicador                  da revista brasileira de ....')
        self.mocker.result(u'PUBLICADOR DA REVISTA BRASILEIRA DE ....')

        mock_normalize_data(u'publicador da revista brasileira de ....')
        self.mocker.result(u'PUBLICADOR DA REVISTA BRASILEIRA DE ....')

        self.mocker.replay()

        journal_and_issue_data = {'journal': {'publisher_name': 'publicador da revista brasileira de ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._normalize_data = mock_normalize_data
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_unmatched(self):
        expected = [validator.STATUS_ERROR, 'publicador da revista brasileira de .... [journal]\npublicador abcdefgh [article]']
        xml = '<root><publisher-name>publicador abcdefgh</publisher-name></root>'

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

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._normalize_data = mock_normalize_data
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_is_missing_in_journal(self):
        expected = [validator.STATUS_ERROR, 'Missing publisher_name in journal']
        xml = '<root><publisher-name>publicador abcdefgh</publisher-name></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {}}
        

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_publisher_name_is_missing_in_article(self):
        expected = [validator.STATUS_ERROR, 'Missing publisher-name in article']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {'publisher_name': 'publicador da revista brasileira de ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))


class FundingGroupValidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', NotifierStub())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)

        vpipe = validator.FundingGroupValidationPipe(data)
        vpipe.configure(_notifier=_notifier,
                        _pkg_analyzer=_pkg_analyzer)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_no_funding_group_and_no_ack(self):
        expected = [validator.STATUS_WARNING, 'no funding-group and no ack']
        xml = '<root></root>'

        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (AttemptStub(), stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_no_funding_group_and_ack_has_no_number(self):
        expected = [validator.STATUS_OK, '<ack>acknowle<sub />dgements</ack>']
        xml = '<root><ack>acknowle<sub/>dgements</ack></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_no_funding_group_and_ack_has_number(self):
        expected = [validator.STATUS_WARNING, '<ack>acknowledgements<p>1234</p></ack> looks to have contract number. If so, it must be identified using funding-group']
        xml = '<root><ack>acknowledgements<p>1234</p></ack></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_funding_group(self):
        expected = [validator.STATUS_OK, '<funding-group>funding data</funding-group>']
        xml = '<root><ack>acknowledgements<funding-group>funding data</funding-group></ack></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))


class NLMJournalTitleValidationPipeTests(mocker.MockerTestCase):
    """
    Tests of NLMJournalTitleValidationPipe
    """
    def _makeOne(self, data, **kwargs):
        from balaio import utils
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)
        #_issn_validator = kwargs.get('_issn_validator', utils.is_valid_issn)

        vpipe = validator.NLMJournalTitleValidationPipe(data)
        vpipe.configure(_scieloapi=_scieloapi,
                        _notifier=_notifier,
                        _sapi_tools=_sapi_tools,
                        _pkg_analyzer=_pkg_analyzer)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_nlm_journal_title_matched(self):
        expected = [validator.STATUS_OK, 'NLM Journal title']
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

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_nlm_journal_title_unmatched(self):
        expected = [validator.STATUS_ERROR, 'NLM Journal Title .... [journal]\nANY Journal Title [article]']
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

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._normalize_data = mock_normalize_data

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_nlm_journal_title_is_missing_in_journal(self):
        expected = [validator.STATUS_OK, 'journal has no NLM journal title']
        xml = '<root><journal-meta><journal-id journal-id-type="nlm-ta">ANY Journal Title</journal-id></journal-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_nlm_journal_title_is_missing_in_article(self):
        expected = [validator.STATUS_ERROR, 'Missing .//journal-meta/journal-id[@journal-id-type="nlm-ta"] in article']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        journal_and_issue_data = {'journal': {'medline_title': 'NLM Journal Title ....'}}

        data = (stub_attempt, stub_package_analyzer, journal_and_issue_data)

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        self.assertEqual(expected,
                         vpipe.validate(data))


class DOIVAlidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', NotifierStub())
        _pkg_analyzer = kwargs.get('_pkg_analyzer', PackageAnalyzerStub)

        vpipe = validator.DOIVAlidationPipe(data)
        vpipe.configure(_notifier=_notifier,
                        _pkg_analyzer=_pkg_analyzer)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_valid_and_matched_DOI(self):
        expected = [validator.STATUS_OK, '']
        xml = '<root><article-id pub-id-type="doi">10.1590/S0001-37652013000100008</article-id></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_doi_validator = self.mocker.mock()
        mock_doi_validator('10.1590/S0001-37652013000100008')
        self.mocker.result(True)

        self.mocker.replay()

        #journal_and_issue_data = {'journal': {'doi': u'10.1590/S0001-37652013000100008'}}

        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._doi_validator = mock_doi_validator

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_invalid_but_matched_DOI(self):
        expected = [validator.STATUS_WARNING, 'DOI is not valid']
        xml = '<root><article-id pub-id-type="doi">10.1590/S0001-37652013000100002</article-id></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_doi_validator = self.mocker.mock()
        mock_doi_validator('10.1590/S0001-37652013000100002')
        self.mocker.result(False)

        self.mocker.replay()

        #journal_and_issue_data = {'journal': {'doi': u'10.1590/S0001-37652013000100002'}}

        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)
        vpipe._doi_validator = mock_doi_validator

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_missing_DOI(self):
        expected = [validator.STATUS_WARNING, 'missing DOI in xml']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        #journal_and_issue_data = {'journal': {'doi': u'10.1590/S0001-37652013000100002'}}

        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(data, _pkg_analyzer=stub_package_analyzer)

        self.assertEqual(expected,
                         vpipe.validate(data))
