import zipfile
from tempfile import NamedTemporaryFile
from xml.etree.ElementTree import ElementTree

import mocker
from balaio import checkin


class SPSMixinTests(mocker.MockerTestCase):

    def _make_test_archive(self, arch_data):
        fp = NamedTemporaryFile()
        with zipfile.ZipFile(fp, 'w') as zipfp:
            for archive, data in arch_data:
                zipfp.writestr(archive, data)

        return fp

    def _makeOne(self, fname):
        class Foo(checkin.SPSMixin, checkin.Xray):
            pass

        return Foo(fname)

    def test_xmls_yields_etree_instances(self):
        data = [('bar.xml', b'<root><name>bar</name></root>')]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        xmls = pkg.xmls
        self.assertIsInstance(xmls.next(), ElementTree)

    def test_xml_returns_etree_instance(self):
        data = [('bar.xml', b'<root><name>bar</name></root>')]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsInstance(pkg.xml, ElementTree)

    def test_xml_raises_AttributeError_when_multiple_xmls(self):
        data = [
            ('bar.xml', b'<root><name>bar</name></root>'),
            ('baz.xml', b'<root><name>baz</name></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertRaises(AttributeError, lambda: pkg.xml)

    def test_meta_journal_title_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><journal-title-group><journal-title>foo</journal-title>\
                </journal-title-group><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['journal_title'], 'foo')

    def test_meta_journal_title_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['journal_title'])

    def test_meta_journal_eissn_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['journal_eissn'], '1234-1234')

    def test_meta_journal_eissn_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="ppub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['journal_eissn'])

    def test_meta_journal_pissn_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="ppub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['journal_pissn'], '1234-1234')

    def test_meta_journal_pissn_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['journal_pissn'])

    def test_meta_article_title_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><title-group><article-title>bar</article-title>\
                   </title-group><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['article_title'], 'bar')

    def test_meta_article_title_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['article_title'])

    def test_meta_issue_year_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><pub-date><year>2013</year></pub-date>\
                                <issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['issue_year'], '2013')

    def test_meta_issue_year_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['issue_year'])

    def test_meta_issue_volume_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><volume>2</volume>\
                         <issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['issue_volume'], '2')

    def test_meta_issue_volume_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['issue_volume'])

    def test_meta_issue_number_data_is_fetched(self):
        data = [
            ('bar.xml', b'<root><issue>2</issue>\
                         <issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertEqual(pkg.meta['issue_number'], '2')

    def test_meta_issue_number_is_None_if_not_present(self):
        data = [
            ('bar.xml', b'<root><issn pub-type="epub">1234-1234</issn></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertIsNone(pkg.meta['issue_number'])

    def test_if_pissn_None_and_if_eissn_None(self):
        data = [
            ('bar.xml', b'<root></root>'),
        ]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertRaises(ValueError, lambda: pkg.meta)


class XrayTests(mocker.MockerTestCase):

    def _make_test_archive(self, arch_data):
        fp = NamedTemporaryFile()
        with zipfile.ZipFile(fp, 'w') as zipfp:
            for archive, data in arch_data:
                zipfp.writestr(archive, data)

        return fp

    def test_non_zip_archive_raises_ValueError(self):
        fp = NamedTemporaryFile()
        self.assertRaises(ValueError, lambda: checkin.Xray(fp.name))

    def test_get_ext_returns_member_names(self):
        arch = self._make_test_archive(
            [('bar.xml', b'<root><name>bar</name></root>')])

        xray = checkin.Xray(arch.name)

        self.assertEquals(xray.get_ext('xml'), ['bar.xml'])

    def test_get_ext_raises_ValueError_when_ext_doesnot_exist(self):
        arch = self._make_test_archive(
            [('bar.xml', b'<root><name>bar</name></root>')])

        xray = checkin.Xray(arch.name)

        self.assertRaises(ValueError, lambda: xray.get_ext('jpeg'))

    def test_get_fps_returns_an_iterable(self):
        arch = self._make_test_archive(
            [('bar.xml', b'<root><name>bar</name></root>')])

        xray = checkin.Xray(arch.name)

        fps = xray.get_fps('xml')
        self.assertTrue(hasattr(fps, 'next'))

    def test_get_fpd_yields_ZipExtFile_instances(self):
        arch = self._make_test_archive(
            [('bar.xml', b'<root><name>bar</name></root>')])

        xray = checkin.Xray(arch.name)

        fps = xray.get_fps('xml')
        self.assertIsInstance(fps.next(), zipfile.ZipExtFile)

    def test_get_fps_swallow_exceptions_when_ext_doesnot_exist(self):
        arch = self._make_test_archive(
            [('bar.xml', b'<root><name>bar</name></root>')])

        xray = checkin.Xray(arch.name)
        fps = xray.get_fps('jpeg')

        self.assertRaises(StopIteration, lambda: fps.next())

