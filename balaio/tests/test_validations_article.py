# coding: utf-8
import unittest
import mocker

from balaio.lib import models, utils
from balaio.lib.validations import article
from balaio.tests.doubles import *


class FundingGroupValidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        vpipe = article.FundingGroupValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_no_funding_group_and_no_ack(self):
        expected = [models.Status.warning, 'Missing data: funding-group, ack']
        xml = '<root></root>'

        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (AttemptStub(), stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_no_funding_group_and_ack_has_no_number(self):
        expected = [models.Status.ok, '<ack>acknowle<sub />dgements</ack>']
        xml = '<root><ack>acknowle<sub/>dgements</ack></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_no_funding_group_and_ack_has_number(self):
        expected = [models.Status.warning, '<ack>acknowledgements<p>1234</p></ack> has numbers. If it is a contract number, it must be identified in funding-group.']
        xml = '<root><ack>acknowledgements<p>1234</p></ack></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_funding_group(self):
        expected = [models.Status.ok, '<funding-group>funding data</funding-group>']
        xml = '<root><ack>acknowledgements<funding-group>funding data</funding-group></ack></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)
        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(xml)

        self.assertEqual(expected,
                         vpipe.validate(data))


class DOIVAlidationPipeTests(mocker.MockerTestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        _doi_validator = kwargs.get('_doi_validator', lambda: False)

        vpipe = article.DOIVAlidationPipe(_notifier, _doi_validator)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_valid_and_matched_DOI(self):
        expected = [models.Status.ok, 'Valid DOI: 10.1590/S0001-37652013000100008']
        xml = '<root><article-id pub-id-type="doi">10.1590/S0001-37652013000100008</article-id></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_doi_validator = self.mocker.mock()
        mock_doi_validator('10.1590/S0001-37652013000100008')
        self.mocker.result(True)

        self.mocker.replay()

        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(data, _doi_validator=mock_doi_validator)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_invalid_but_matched_DOI(self):
        expected = [models.Status.warning, 'DOI is not registered: 10.1590/S0001-37652013000100002']
        xml = '<root><article-id pub-id-type="doi">10.1590/S0001-37652013000100002</article-id></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_doi_validator = self.mocker.mock()
        mock_doi_validator('10.1590/S0001-37652013000100002')
        self.mocker.result(False)

        self.mocker.replay()

        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(data, _doi_validator=mock_doi_validator)

        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_missing_DOI(self):
        expected = [models.Status.warning, 'Missing data: DOI']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, {})

        vpipe = self._makeOne(data)

        self.assertEqual(expected,
                         vpipe.validate(data))


class ArticleSectionValidationPipeTests(mocker.MockerTestCase):
    """
    Tests of ArticleSectionValidationPipe
    """
    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        _normalize_data = kwargs.get('_normalize_data', utils.normalize_data)

        vpipe = article.ArticleSectionValidationPipe(_notifier, _normalize_data)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def _issue_data(self):
        # isso deveria ser um dict no lugar de uma lista, mas a api retorna assim
        dict_item1 = {u'titles': [
            [u'es', u'Artículos Originales'],
            [u'en', u'Original Articles'],
        ]}
        dict_item2 = {u'titles': [
            [u'es', u'Editorial'],
            [u'en', u'Editorial'],
        ]}
        return {u'sections': [dict_item1, dict_item2], u'label': '1(1)'}

    def test_article_section_matched(self):
        expected = [models.Status.ok, u'Valid article section: Original Articles']
        #article-categories/subj-group[@subj-group-type=”heading”]
        xml = '<root><article-meta><article-categories><subj-group subj-group-type="heading"><subject>Original Articles</subject></subj-group></article-categories></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_is_a_registered_section_title = self.mocker.mock()
        mock_is_a_registered_section_title(self._issue_data()['sections'], u'Original Articles')
        self.mocker.result(True)

        self.mocker.replay()

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        vpipe._is_a_registered_section_title = mock_is_a_registered_section_title
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_section_is_not_registered(self):
        expected = [models.Status.error, u'Mismatched data: Articles. Expected one of Artículos Originales | Original Articles | Editorial | Editorial']
        xml = '<root><article-meta><article-categories><subj-group subj-group-type="heading"><subject>Articles</subject></subj-group></article-categories></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        mock_is_a_registered_section_title = self.mocker.mock()
        mock_is_a_registered_section_title(self._issue_data()['sections'], u'Articles')
        self.mocker.result(False)

        self.mocker.replay()

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        #vpipe._normalize_data = mock_normalize_data
        vpipe._is_a_registered_section_title = mock_is_a_registered_section_title
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_section_is_missing_in_article(self):
        expected = [models.Status.warning, u'Missing data: article section']
        xml = '<root></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))


class ArticleMetaPubDateValidationPipeTests(mocker.MockerTestCase):
    """
    Tests of ArticleSectionValidationPipe
    """
    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)

        vpipe = article.ArticleMetaPubDateValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def _issue_data(self, year=1999, start=9, end=0):
        return {'publication_end_month': end,
                'publication_start_month': start,
                'publication_year': year}

    def test_article_pubdate_matched(self):
        expected = [models.Status.ok, 'Valid publication date: 9/1999']
        #article-categories/subj-group[@subj-group-type=”heading”]
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>09</month><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_pubdate_matched_month_is_name(self):
        expected = [models.Status.ok, 'Valid publication date: Sep/1999']
        #article-categories/subj-group[@subj-group-type=”heading”]
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>Sep</month><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_pubdate_matched_month_range(self):
        expected = [models.Status.ok, 'Valid publication date: Jan-Mar/1999']
        #article-categories/subj-group[@subj-group-type=”heading”]
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><season>Jan-Mar</season><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data(1999, 1, 3))

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_multiple_pubdate_matched(self):
        expected = [models.Status.ok, 'Valid publication date: 9/1999']
        #article-categories/subj-group[@subj-group-type=”heading”]
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><month>11</month><year>1999</year></pub-date>        <pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>09</month><year>1999</year></pub-date></article-meta></root>'
        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_multiple_pubdate_matched_month_is_name(self):
        expected = [models.Status.ok, 'Valid publication date: Sep/1999']
        #article-categories/subj-group[@subj-group-type=”heading”]
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><month>11</month><year>1999</year></pub-date><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>Sep</month><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_multiple_pubdate_matched_month_range(self):
        expected = [models.Status.ok, 'Valid publication date: Sep/1999']
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>Sep</month><year>1999</year></pub-date><pub-date pub-type="pub" iso-8601-date="1999-03-27"><month>Oct</month><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_pubdate_unmatched(self):
        expected = [models.Status.error, 'Mismatched data: 8/1999. Expected one of Sep/1999 | 9/1999']
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>08</month><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))

    def test_article_multiple_pubdate_unmatched_month_range(self):
        expected = [models.Status.error, 'Mismatched data: Sep/2000 | Nov/1999. Expected one of Sep/1999 | 9/1999']
        xml = '<root><article-meta><pub-date pub-type="pub" iso-8601-date="1999-03-27"><day>27</day><month>Sep</month><year>2000</year></pub-date><pub-date pub-type="pub" iso-8601-date="1999-03-27"><month>Nov</month><year>1999</year></pub-date></article-meta></root>'

        stub_attempt = AttemptStub()
        stub_package_analyzer = self._makePkgAnalyzerWithData(xml)

        data = (stub_attempt, stub_package_analyzer, self._issue_data())

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate(data))


class LicenseValidationPipeTests(mocker.MockerTestCase):
    """
    Tests of LicenseValidationPipe
    """
    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)

        vpipe = article.LicenseValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_article_with_valid_license(self):
        expected = [models.Status.ok, 'This article have a valid license']
        data = '<root><article-meta><permissions><license-p>This is an Open Access article distributed under the terms of the Creative Commons...</license-p></permissions></article-meta></root>'

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate([None, pkg_analyzer_stub, None]))

    def test_article_without_permissions(self):
        expected = [models.Status.error, 'Missing data: permissions']
        data = '<root><article-meta></article-meta></root>'

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate([None, pkg_analyzer_stub, None]))

    def test_article_without_text_license(self):
        expected = [models.Status.warning, 'This article dont have a license']
        data = '<root><article-meta><permissions><license-p></license-p></permissions></article-meta></root>'

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        vpipe = self._makeOne(data)
        self.assertEqual(expected,
                         vpipe.validate([None, pkg_analyzer_stub, None]))

