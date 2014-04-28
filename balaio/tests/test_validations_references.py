# coding: utf-8
import unittest
import mocker

from balaio.lib import models, utils
from balaio.lib.validations import references
from balaio.tests.doubles import *


class ReferenceSourceValidationTests(unittest.TestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)
        vpipe = references.ReferenceSourceValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_reference_list_with_valid_tag_source(self):
        expected = [models.Status.ok, 'Valid data: source']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_missing_tag_source(self):
        expected = [models.Status.error, 'Missing data: source. (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
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
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_two_missing_tag_source(self):
        expected = [models.Status.error, 'Missing data: source. (B23, B24)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <year>2013</year>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
                <ref id="B24">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
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
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_tag_source_missing_content(self):
        expected = [models.Status.error, 'Missing data: source. (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source></source>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)


class ReferenceValidationPipeTests(unittest.TestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)

        vpipe = references.ReferenceValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_reference_with_valid_tag_ref(self):
        expected = [models.Status.ok, 'Found 1 references']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_with_missing_tag_ref(self):
        expected = [models.Status.warning, 'Missing data: references']
        data = '''
            <root>
              <ref-list>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)


class ReferenceJournalTypeArticleTitleValidationTests(unittest.TestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)

        vpipe = references.ReferenceJournalTypeArticleTitleValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_reference_list_with_valid_tag_article_title(self):
        expected = [models.Status.ok, 'Valid data: article-title']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_missing_tag_article_title(self):
        expected = [models.Status.error, 'Missing data: article-title. (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <year>2013</year>
                    <volume>49</volume>
                    <source><![CDATA[Palaeontology]]></source>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_two_missing_tag_article_title(self):
        expected = [models.Status.error, 'Missing data: article-title. (B23, B24)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <year>2013</year>
                    <volume>49</volume>
                    <source><![CDATA[Palaeontology]]></source>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
                <ref id="B24">
                  <element-citation publication-type="journal">
                    <year>2013</year>
                    <volume>49</volume>
                    <source><![CDATA[Palaeontology]]></source>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_tag_source_missing_content(self):
        expected = [models.Status.error, 'Missing data: article-title. (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)


class ReferenceDateValidationTests(unittest.TestCase):

    def _makeOne(self, data, **kwargs):
        _notifier = kwargs.get('_notifier', lambda: NotifierStub)

        vpipe = references.ReferenceYearValidationPipe(_notifier)
        vpipe.feed(data)
        return vpipe

    def _makePkgAnalyzerWithData(self, data):
        pkg_analyzer_stub = PackageAnalyzerStub()
        pkg_analyzer_stub._xml_string = data
        return pkg_analyzer_stub

    def test_reference_list_with_valid_tag_year(self):
        expected = [models.Status.ok, 'Valid data: year']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <year>2013</year>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_valid_and_well_format_tag_year(self):
        expected = [models.Status.ok, 'Valid data: year']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <year>2013</year>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_valid_and_not_well_format_tag_year(self):
        expected = [models.Status.error, 'Invalid value for year: 13 (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"><![CDATA[Title]]></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <year>13</year>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_missing_tag_year(self):
        expected = [models.Status.error, 'Missing data: year. (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <volume>49</volume>
                    <source><![CDATA[Palaeontology]]></source>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_two_missing_tag_year(self):
        expected = [models.Status.error, 'Missing data: year. (B23, B24)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <volume>49</volume>
                    <source><![CDATA[Palaeontology]]></source>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
                <ref id="B24">
                  <element-citation publication-type="journal">
                    <volume>49</volume>
                    <source><![CDATA[Palaeontology]]></source>
                    <page-range>641-46</page-range>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

    def test_reference_list_with_tag_year_missing_content(self):
        expected = [models.Status.error, 'Missing data: year. (B23)']
        data = '''
            <root>
              <ref-list>
                <ref id="B23">
                  <element-citation publication-type="journal">
                    <article-title xml:lang="en"></article-title>
                    <source><![CDATA[Palaeontology]]></source>
                    <volume>49</volume>
                    <page-range>641-46</page-range>
                    <year></year>
                  </element-citation>
                </ref>
              </ref-list>
            </root>'''

        vpipe = self._makeOne(data)
        pkg_analyzer_stub = self._makePkgAnalyzerWithData(data)

        self.assertEquals(
            vpipe.validate([None, pkg_analyzer_stub, None]), expected)

