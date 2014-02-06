#coding: utf-8
import os
import zipfile
from tempfile import NamedTemporaryFile

import mocker
import unittest

from balaio import package
from . import doubles


SAMPLE_PACKAGE = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)),
    '..', '..', 'samples', '0042-9686-bwho-91-08-545.zip'))


class PackageAnalyzerTests(mocker.MockerTestCase):

    def _make_test_archive(self, arch_data):
        fp = NamedTemporaryFile()
        with zipfile.ZipFile(fp, 'w') as zipfp:
            for archive, data in arch_data:
                zipfp.writestr(archive, data)

        return fp

    def _makeOne(self, fname):
        return package.PackageAnalyzer(fname)

    def test_package_checksum_is_calculated(self):
        data = [('bar.xml', b'<root><name>bar</name></root>')]
        arch1 = self._make_test_archive(data)
        arch2 = self._make_test_archive(data)

        self.assertEquals(
            self._makeOne(arch1.name).checksum,
            self._makeOne(arch2.name).checksum
        )

    def test_is_subclass_of_spsmixin_and_xray(self):
        self.assertTrue(issubclass(package.PackageAnalyzer, package.xray.Xray))
        self.assertTrue(issubclass(package.PackageAnalyzer, package.xray.SPSMixin))

    def test_package_is_locked_during_context(self):
        import os, stat

        data = [('bar.xml', b'<root><name>bar</name></root>')]
        arch = self._make_test_archive(data)

        out_context_perm = stat.S_IMODE(os.stat(arch.name).st_mode)

        with package.PackageAnalyzer(arch.name) as pkg:
            in_context_perm = stat.S_IMODE(os.stat(arch.name).st_mode)
            self.assertTrue(out_context_perm != in_context_perm)

        self.assertEqual(out_context_perm, stat.S_IMODE(os.stat(arch.name).st_mode))

    def test_package_remove_user_write_perm_during_context(self):
        import os, stat

        data = [('bar.xml', b'<root><name>bar</name></root>')]
        arch = self._make_test_archive(data)

        with package.PackageAnalyzer(arch.name) as pkg:
            in_context_perm = oct(stat.S_IMODE(os.stat(arch.name).st_mode))
            for forbidden_val in ['3', '6', '7']:
                self.assertNotEqual(in_context_perm[1], forbidden_val)

    def test_is_valid_schema_with_valid_xml(self):
        data = [('bar.xml', b'''<?xml version="1.0" encoding="utf-8"?>
                <article article-type="in-brief" dtd-version="1.0" xml:lang="en" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">
                <front>
                    <journal-meta>
                        <journal-id journal-id-type="nlm-ta">Bull World Health Organ</journal-id>
                        <journal-title-group>
                            <journal-title>Bulletin of the World Health Organization</journal-title>
                            <abbrev-journal-title abbrev-type="pubmed">Bull. World Health Organ.</abbrev-journal-title>
                        </journal-title-group>
                        <issn pub-type="ppub">0042-9686</issn>
                        <publisher>
                            <publisher-name>World Health Organization</publisher-name>
                        </publisher>
                    </journal-meta>
                    <article-meta>
                        <article-id pub-id-type="publisher-id">BLT.13.000813</article-id>
                        <article-id pub-id-type="doi">10.2471/BLT.13.000813</article-id>
                        <article-categories>
                            <subj-group subj-group-type="heading">
                                <subject> In This Month´s Bulletin</subject>
                            </subj-group>
                        </article-categories>
                        <title-group>
                            <article-title>In this month's <italic>Bulletin</italic>
                            </article-title>
                        </title-group>
                        <pub-date pub-type="ppub">
                            <month>08</month>
                            <year>2013</year>
                        </pub-date>
                        <volume>91</volume>
                        <issue>8</issue>
                        <fpage>545</fpage>
                        <lpage>545</lpage>
                        <permissions>
                            <copyright-statement>(c) World Health Organization (WHO) 2013. All rights reserved.</copyright-statement>
                            <copyright-year>2013</copyright-year>
                        </permissions>
                    </article-meta>
                </front>
                <body>
                    <p>In the editorial section, David B Evans and colleagues (546) discuss the dimensions of universal health coverage. In the news, Gary Humphreys &#x26; Catherine Fiankan-Bokonga (549&#x2013;550) report on the approach France is taking to counter trends in childhood obesity. Fiona Fleck (551&#x2013;552) interviews Philip James on how the global obesity epidemic started and what should be done to reverse it.</p>
                    <sec sec-type="other1">
                        <title>Nigeria</title>
                    </sec>
                </body>
            </article>
            ''')]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertTrue(pkg.is_valid_schema())

    def test_is_valid_schema_with_invalid_xml(self):
        data = [('bar.xml', b'''<?xml version="1.0" encoding="utf-8"?>
                <article article-type="in-brief" dtd-version="1.0" xml:lang="en" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">
                <front>
                    <journal-meta>
                        <journal-title-group>
                            <journal-title>Bulletin of the World Health Organization</journal-title>
                            <abbrev-journal-title abbrev-type="pubmed">Bull. World Health Organ.</abbrev-journal-title>
                        </journal-title-group>
                        <issn pub-type="ppub">0042-9686</issn>
                        <publisher>
                            <publisher-name>World Health Organization</publisher-name>
                        </publisher>
                    </journal-meta>
                    <article-meta>
                        <article-id pub-id-type="publisher-id">BLT.13.000813</article-id>
                        <article-id pub-id-type="doi">10.2471/BLT.13.000813</article-id>
                        <article-categories>
                            <subj-group subj-group-type="heading">
                                <subject> In This Month´s Bulletin</subject>
                            </subj-group>
                        </article-categories>
                        <title-group>
                            <article-title>In this month's <italic>Bulletin</italic>
                            </article-title>
                        </title-group>
                        <pub-date pub-type="ppub">
                            <month>08</month>
                            <year>2013</year>
                        </pub-date>
                        <volume>91</volume>
                        <issue>8</issue>
                        <fpage>545</fpage>
                        <lpage>545</lpage>
                        <permissions>
                            <copyright-statement>(c) World Health Organization (WHO) 2013. All rights reserved.</copyright-statement>
                            <copyright-year>2013</copyright-year>
                        </permissions>
                    </article-meta>
                </front>
                <body>
                    <p>In the editorial section, David B Evans and colleagues (546) discuss the dimensions of universal health coverage. In the news, Gary Humphreys &#x26; Catherine Fiankan-Bokonga (549&#x2013;550) report on the approach France is taking to counter trends in childhood obesity. Fiona Fleck (551&#x2013;552) interviews Philip James on how the global obesity epidemic started and what should be done to reverse it.</p>
                    <sec sec-type="other1">
                        <title>Nigeria</title>
                    </sec>
                </body>
            </article>
            ''')]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertFalse(pkg.is_valid_schema())

    def test_is_valid_schema_with_wrong_tag(self):
        data = [('bar.xml', b'''<?xml version="1.0" encoding="utf-8"?>
                <article article-type="in-brief" dtd-version="1.0" xml:lang="en" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">
                <front>
                    <a>wrong</a>
                    <journal-meta>
                        <journal-title-group>
                            <journal-title>Bulletin of the World Health Organization</journal-title>
                            <abbrev-journal-title abbrev-type="pubmed">Bull. World Health Organ.</abbrev-journal-title>
                        </journal-title-group>
                        <issn pub-type="ppub">0042-9686</issn>
                        <publisher>
                            <publisher-name>World Health Organization</publisher-name>
                        </publisher>
                    </journal-meta>
                    <article-meta>
                        <article-id pub-id-type="publisher-id">BLT.13.000813</article-id>
                        <article-id pub-id-type="doi">10.2471/BLT.13.000813</article-id>
                        <article-categories>
                            <subj-group subj-group-type="heading">
                                <subject> In This Month´s Bulletin</subject>
                            </subj-group>
                        </article-categories>
                        <title-group>
                            <article-title>In this month's <italic>Bulletin</italic>
                            </article-title>
                        </title-group>
                        <pub-date pub-type="ppub">
                            <month>08</month>
                            <year>2013</year>
                        </pub-date>
                        <volume>91</volume>
                        <issue>8</issue>
                        <fpage>545</fpage>
                        <lpage>545</lpage>
                        <permissions>
                            <copyright-statement>(c) World Health Organization (WHO) 2013. All rights reserved.</copyright-statement>
                            <copyright-year>2013</copyright-year>
                        </permissions>
                    </article-meta>
                </front>
                <body>
                    <p>In the editorial section, David B Evans and colleagues (546) discuss the dimensions of universal health coverage. In the news, Gary Humphreys &#x26; Catherine Fiankan-Bokonga (549&#x2013;550) report on the approach France is taking to counter trends in childhood obesity. Fiona Fleck (551&#x2013;552) interviews Philip James on how the global obesity epidemic started and what should be done to reverse it.</p>
                    <sec sec-type="other1">
                        <title>Nigeria</title>
                    </sec>
                </body>
            </article>
            ''')]
        arch = self._make_test_archive(data)
        pkg = self._makeOne(arch.name)

        self.assertFalse(pkg.is_valid_schema())


class SafePackageTests(mocker.MockerTestCase):
    def test_primary_path(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')

        self.assertEqual(safe_pkg.primary_path, SAMPLE_PACKAGE)

    def test_analyzer_context(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')
        mock_panalyzer = self.mocker.replace(package.PackageAnalyzer)

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')

        mock_panalyzer(mocker.ANY)
        self.mocker.result(doubles.PackageAnalyzerStub())

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')
        with safe_pkg.analyzer as safe_context:
            self.assertEqual(safe_context.checksum,
                             '5a74db5db860f2f8e3c6a5c64acdbf04')

    @unittest.skip('uuid.uuid4() Performed more times than expected')
    def test_gen_safe_path(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')
        self.mocker.count(2)  # 2 times cause we are calling the function directly.

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')

        self.assertEqual(safe_pkg._gen_safe_path(), '/tmp/e7d0213c44ba4ed5adcde9e3fdf62963.zip')

    def test_mark_as_failed_can_be_silenced(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')
        mock_utils = self.mocker.replace('balaio.utils')

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')

        mock_utils.mark_as_failed(mocker.ANY)
        self.mocker.throw(OSError)

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')

        self.assertIsNone(safe_pkg.mark_as_failed(silence=True))

    def test_mark_as_failed_not_silenced_by_default(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')
        mock_utils = self.mocker.replace('balaio.utils')

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')

        mock_utils.mark_as_failed(mocker.ANY)
        self.mocker.throw(OSError)

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')

        self.assertRaises(OSError, lambda: safe_pkg.mark_as_failed())

    def test_mark_as_duplicated_can_be_silenced(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')
        mock_utils = self.mocker.replace('balaio.utils')

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')

        mock_utils.mark_as_duplicated(mocker.ANY)
        self.mocker.throw(OSError)

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')

        self.assertIsNone(safe_pkg.mark_as_duplicated(silence=True))

    def test_mark_as_duplicated_not_silenced_by_default(self):
        # mocks
        mock_shutil = self.mocker.replace('shutil')
        mock_uuid4 = self.mocker.replace('uuid.uuid4')
        mock_utils = self.mocker.replace('balaio.utils')

        mock_shutil.copy2(mocker.ANY, mocker.ANY)
        self.mocker.result(None)

        mock_uuid4().hex
        self.mocker.result('e7d0213c44ba4ed5adcde9e3fdf62963')

        mock_utils.mark_as_duplicated(mocker.ANY)
        self.mocker.throw(OSError)

        self.mocker.replay()

        safe_pkg = package.SafePackage(SAMPLE_PACKAGE, '/tmp/')

        self.assertRaises(OSError, lambda: safe_pkg.mark_as_duplicated())

