#coding: utf-8
import os
import zipfile
from tempfile import NamedTemporaryFile

import unittest
import transaction

from balaio.lib import checkin, models, excepts, package
from .utils import db_bootstrap, DB_READY
from . import doubles


SAMPLE_PACKAGE = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)),
    '..', '..', 'samples', '0042-9686-bwho-91-08-545.zip'))


@unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
class CheckinTests(unittest.TestCase):

    def setUp(self):
        self.engine = db_bootstrap()
        self.session = models.Session()

    def tearDown(self):
        models.Base.metadata.drop_all(self.engine)

    def _make_test_archive(self, arch_data):
        fp = NamedTemporaryFile()
        with zipfile.ZipFile(fp, 'w') as zipfp:
            for archive, data in arch_data:
                zipfp.writestr(archive, data)

        return fp

    def test_get_attempt_ok(self):
        """
        Attempt generates fine
        """
        safe_package = doubles.SafePackageStub(SAMPLE_PACKAGE, '/tmp/')
        self.assertIsInstance(checkin.get_attempt(safe_package),
            models.Attempt)

    def test_accessing_generated_attempt_data(self):
        """
        Attempt generates fine
        """
        safe_package = doubles.SafePackageStub(SAMPLE_PACKAGE, '/tmp/')
        attempt = checkin.get_attempt(safe_package)
        # this filepath was got from doubles.PackageAnalyzerStub
        self.assertTrue('/tmp/bla.zip' in attempt.filepath)

    def test_get_attempt_failure(self):
        """
        Attempt is already registered
        """
        safe_package = doubles.SafePackageStub(SAMPLE_PACKAGE, '/tmp/')
        self.assertIsInstance(checkin.get_attempt(safe_package),
            models.Attempt)
        self.assertRaises(excepts.DuplicatedPackage,
            lambda: checkin.get_attempt(safe_package))

    def test_get_attempt_article_title_is_already_registered(self):
        """
        There are more than one article registered with same article title
        """
        pkg = package.PackageAnalyzer(SAMPLE_PACKAGE)
        article = models.ArticlePkg(**pkg.meta)
        self.session.add(article)
        transaction.commit()

        article2 = models.ArticlePkg(**pkg.meta)
        article2.journal_title = 'REV'
        self.session.add(article2)
        transaction.commit()

        safe_package = doubles.SafePackageStub(SAMPLE_PACKAGE, '/tmp/')
        attempt = checkin.get_attempt(safe_package)
        self.assertIsInstance(attempt, models.Attempt)

    def test_get_attempt_invalid_package_missing_xml(self):
        """
        There are more than one article registered with same article title
        """
        pkg = self._make_test_archive([('texto.txt', b'bla bla')])
        safe_package = package.SafePackage(pkg.name, '/tmp/')
        self.assertRaises(ValueError, checkin.get_attempt, safe_package)

    def test_get_attempt_invalid_package_missing_issn_and_article_title(self):
        """
        Package is invalid because there is no ISSN and article_title
        """
        pkg = self._make_test_archive([('texto.xml', b'<root/>')])
        safe_package = package.SafePackage(pkg.name, '/tmp/')
        self.assertRaises(ValueError, lambda: checkin.get_attempt(safe_package))
