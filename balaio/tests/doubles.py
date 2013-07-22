# coding: utf-8
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree
import types


class Patch(object):
    """
    Helps patching instances to ease testing.
    """
    def __init__(self, target_object, target_attrname, patch):
        self.target_object = target_object
        self.target_attrname = target_attrname
        if callable(patch):
            self.patch = types.MethodType(patch, target_object, target_object.__class__)
        else:
            self.patch = patch
        self._toggle()

    def _toggle(self):
        self._x = getattr(self.target_object, self.target_attrname)

        setattr(self.target_object, self.target_attrname, self.patch)
        self.patch = self._x

    def __enter__(self):
        return self.target_object

    def __exit__(self, *args, **kwargs):
        self._toggle()


#
# Stubs are test doubles to be used when the test does not aim
# to check inner aspects of a collaboration.
#
class ScieloAPIClientStub(object):
    def __init__(self, *args, **kwargs):
        self.journals = EndpointStub()


class EndpointStub(object):

    def get(self, *args, **kwargs):
        return {}

    def filter(self, *args, **kwargs):
        return (_ for _ in range(5))

    def all(self, *args, **kwargs):
        return (_ for _ in range(5))


class NotifierStub(object):
    def __init__(self, *args, **kwargs):
        pass

    def validation_event(self, *args, **kwargs):
        pass


class PackageAnalyzerStub(object):
    def __init__(self, *args, **kwargs):
        """
        `_xml_string` needs to be patched.
        """
        self._xml_string = None

    @property
    def xml(self):
        etree = ElementTree()
        return etree.parse(StringIO(self._xml_string))

    def lock_package(self):
        return None


class ScieloAPIToolbeltStub(object):
    """
    The real implementation is not based on a class, but has the same API.
    """
    @staticmethod
    def has_any(dataset):
        return True

    @staticmethod
    def get_one(dataset):
        return dataset[0]


class ArticlePkgStub(object):
    def __init__(self, *args, **kwargs):
        self.journal_pissn = '0100-879X'
        self.journal_eissn = '0100-879X'


class AttemptStub(object):
    def __init__(self, *args, **kwargs):
        self.articlepkg = ArticlePkgStub()
        self.filepath = '/tmp/foo/bar.zip'


class ConfigStub(object):
    pass


class PipeStub(object):
    def __init__(self, data, **kwargs):
        self.data = data

    def __iter__(self):
        for i in self.data:
            yield i

