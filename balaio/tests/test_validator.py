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
class PISSNValidationPipeTests(unittest.TestCase):
    def _makeOne(self, data, **kwargs):
        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())

        vpipe = validator.PISSNValidationPipe(data)
        vpipe.configure(_scieloapi=_scieloapi,
                        _notifier=_notifier,
                        _sapi_tools=_sapi_tools)
        return vpipe

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
        expected = ['warning', 'print ISSN is invalid or unknown']
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


    def test_valid_and_known_ISSN(self):
        expected = ['ok', '']
        data = "<root><issn pub-type='ppub'>0102-6720</issn></root>"

        scieloapitoolbelt_stub = get_ScieloAPIToolbeltStubModule()
        scieloapitoolbelt_stub.has_any = lambda x: True

        vpipe = self._makeOne(data, _sapi_tools=scieloapitoolbelt_stub)

        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_valid_and_unknown_ISSN(self):
        expected = ['warning', 'print ISSN is invalid or unknown']
        data = "<root><issn pub-type='ppub'>0102-6720</issn></root>"

        scieloapitoolbelt_stub = get_ScieloAPIToolbeltStubModule()
        scieloapitoolbelt_stub.has_any = lambda x: False

        vpipe = self._makeOne(data, _sapi_tools=scieloapitoolbelt_stub)

        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)


class EISSNValidationPipeTests(unittest.TestCase):
    def _makeOne(self, data, **kwargs):
        vpipe =  validator.EISSNValidationPipe(data)

        _scieloapi = kwargs.get('_scieloapi', ScieloAPIClientStub())
        _notifier = kwargs.get('_notifier', NotifierStub())
        _sapi_tools = kwargs.get('_sapi_tools', get_ScieloAPIToolbeltStubModule())

        vpipe.configure(_scieloapi=_scieloapi,
                        _notifier=_notifier,
                        _sapi_tools=_sapi_tools)
        return vpipe

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
        expected = ['error', 'electronic ISSN is invalid or unknown']
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

    def test_valid_and_known_ISSN(self):
        expected = ['ok', '']
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapitoolbelt_stub = get_ScieloAPIToolbeltStubModule()
        scieloapitoolbelt_stub.has_any = lambda x: True

        vpipe = self._makeOne(data, _sapi_tools=scieloapitoolbelt_stub)

        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)

    def test_valid_and_unknown_ISSN(self):
        expected = ['error', 'electronic ISSN is invalid or unknown']
        data = "<root><issn pub-type='epub'>0102-6720</issn></root>"

        scieloapitoolbelt_stub = get_ScieloAPIToolbeltStubModule()
        scieloapitoolbelt_stub.has_any = lambda x: False

        vpipe = self._makeOne(data, _sapi_tools=scieloapitoolbelt_stub)

        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate(pkg_analyzer_stub), expected)


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
        expected = ['ok', '']
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
        expected = ['warning', 'this xml does not have reference list']
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
        expected = ['error', 'missing content on reference tags: source, article-title or year']
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
        expected = ['error', 'missing some tag in reference list']
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

