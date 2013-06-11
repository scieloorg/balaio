#coding: utf-8
import os
import sys
import stat
import zipfile
import itertools
import xml.etree.ElementTree as etree

import models
from utils import Configuration


config = Configuration.from_env()


class SPSMixin(object):

    @property
    def xmls(self):
        fps = self.get_fps('xml')
        for fp in fps:
            yield etree.parse(fp)

    @property
    def xml(self):
        xmls = list(itertools.islice(self.xmls, 2))
        if len(xmls) == 1:
            return xmls[0]
        else:
            raise AttributeError('there is not a single xml file')

    @property
    def meta(self):
        dct_mta = {}

        xml_nodes = {"journal_title": ".//journal-title-group/journal-title",
                     "journal_eissn": ".//issn[@pub-type='epub']",
                     "journal_pissn": ".//issn[@pub-type='ppub']",
                     "article_title": ".//title-group/article-title",
                     "issue_year": ".//pub-date/year",
                     "issue_volume": ".//volume",
                     "issue_number": ".//issue",
                     }

        for node_k, node_v in xml_nodes.items():
            node = self.xml.find(node_v)
            dct_mta[node_k] = getattr(node, 'text', None)

        return dct_mta


class Xray(object):

    def __init__(self, filename):
        self._filename = filename
        self._zip_pkg = zipfile.ZipFile(filename, 'r')
        self._pkg_names = {}

        self._classify()

    def __del__(self):
        self._cleanup_package_fp()

    def _cleanup_package_fp(self):
        self._zip_pkg.close()

    def _classify(self):
        for fileinfo, filename in zip(self._zip_pkg.infolist(), self._zip_pkg.namelist()):
            # ignore directories and empty files
            if fileinfo.file_size:
                _, ext = filename.rsplit('.', 1)
                ext_node = self._pkg_names.setdefault(ext, [])
                ext_node.append(filename)

    def get_ext(self, ext):
        try:
            return self._pkg_names[ext]
        except KeyError:
            raise AttributeError("the package does not contain a '%s' file" % ext)

    def get_fps(self, ext):

        filenames = self.get_ext(ext)

        for filename in filenames:
            yield self._zip_pkg.open(filename, 'r')


class PackageAnalyzer(SPSMixin, Xray):

    def __init__(self, *args):
        super(PackageAnalyzer, self).__init__(*args)
        self._errors = set()
        self._default_perms = stat.S_IMODE(os.stat(self._filename).st_mode)
        self._is_locked = False

    def __enter__(self):
        self.lock_package()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.restore_perms()
        self._cleanup_package_fp()
        if not self._is_valid():
            self.rename_package()

    @property
    def errors(self):
        """
        Returns a tuple of errors
        """
        return tuple(self._errors)

    def is_valid_package(self):
        """
        Validate if exist at least one xml file and one pdf file
        """
        is_valid = True
        for ext in ['xml', 'pdf']:
            try:
                _ = self.get_ext(ext)
            except AttributeError, e:
                self._errors.add(e.message)
                is_valid = False

        return is_valid

    def lock_package(self):
        """
        Removes the write permission for Others.
        http://docs.python.org/2/library/stat.html#stat.S_IWOTH
        """
        if not self._is_locked:
            perm = self._default_perms ^ stat.S_IWOTH
            os.chmod(self._filename, perm)
            self._is_locked = True

    def restore_perms(self):
        os.chmod(self._filename, self._default_perms)
        self.is_locked = False

    def rename_package(self, prefix='__failed__'):
        os.rename(self._filename, prefix + self._filename)


def get_attempt(package):
    """
    Always returns a brand new models.Attempt instance, bound to
    the expected models.ArticlePkg instance.
    """
    with PackageAnalyzer(package) as pkg_alz:

        if pkg_alz.is_valid_package():

            art = models.get_or_create(models.ArticlePkg, **pkg_alz.meta)

            #Function in utils.py
            pkg_hash = make_digest_file(pkg_alz._zip_pkg)

            attempt_meta = {'package_md5': pkg_hash,
                            'articlepkg_id': art.id}

            attempt = models.get_or_create(models.Attempt, **attempt_meta)

            return attempt
        else:
            sys.stdout.write("Invalid package: %s\n" % pkg_alz.errors)
