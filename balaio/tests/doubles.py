# coding: utf-8
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree
import types


class Patch(object):
    """
    Helps patching instances to ease testing.
    """
    def __init__(self, target_object, target_attrname, patch, instance_method=False):
        self.target_object = target_object
        self.target_attrname = target_attrname
        if callable(patch) and instance_method:
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
        self.issues = EndpointStub()

        def fetch_relations(dataset):
            return dataset
        self.fetch_relations = fetch_relations


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


def get_ScieloAPIToolbeltStubModule():
    """
    Factory of scieloapitoolbelt modules. Using a factory
    is easier to keep the tests isolated.
    """
    sapi_tools = types.ModuleType('scieloapitoolbelt')

    def has_any(dataset):
        return True
    sapi_tools.has_any = has_any

    def get_one(dataset):
        return dataset[0]
    sapi_tools.get_one = get_one

    return sapi_tools


class ArticlePkgStub(object):
    def __init__(self, *args, **kwargs):
        self.journal_pissn = '0100-879X'
        self.journal_eissn = '0100-879X'
        self.issue_volume = '31'
        self.issue_number = '1'
        self.issue_suppl_volume = None
        self.issue_suppl_number = None

    def to_dict(self):
        return dict(id=3,
                    package_checksum='876',
                    articlepkg_id=5,
                    collection_uri='///',
                    started_at=None,
                    finished_at=None,
                    filepath=None,
                    is_valid=True
                    )


class AttemptStub(object):
    def __init__(self, *args, **kwargs):
        self.articlepkg = ArticlePkgStub()
        self.filepath = '/tmp/foo/bar.zip'

    def to_dict(self):
        return dict(id=1,
                    package_checksum='1212',
                    articlepkg_id=1,
                    collection_uri='/',
                    started_at='started_at',
                    finished_at='finished_at',
                    filepath=self.filepath,
                    is_valid=True
                    )


class ConfigStub(object):
    pass


class PipeStub(object):
    def __init__(self, data, **kwargs):
        self.data = data

    def __iter__(self):
        for i in self.data:
            yield i
