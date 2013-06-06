#coding: utf-8
import os
import models
import zipfile
import itertools
import xml.etree.ElementTree as etree


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
                     }

        for node_k, node_v in xml_nodes.items():
            dct_mta[node_k] = self.xml.find(node_v).text

        return dct_mta


class Xray(object):

    def __init__(self, filename):
        self._filename = filename
        self._zip_pkg = zipfile.ZipFile(filename, 'r')
        self._pkg_names = {}

        self._classify()

    def __del__(self):
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
        try:
            self.get_ext('xml')
            self.get_ext('pdf')
            return True
        except AttributeError, e:
            self.errors.add(e.message)
            return False


def get_attempt(package):
    pkg_alz = PackageAnalyzer(package)

    if pkg_alz.is_valid_package():
        os.chmod(pkg_alz._filename, 0770)
        article = models.ArticlePkg(**pkg_alz.meta)
        #Persist this object
