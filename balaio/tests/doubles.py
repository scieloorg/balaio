# coding: utf-8
import os
import types
import datetime
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree

from balaio.lib import utils, package


HERE = os.path.dirname(os.path.abspath(__file__))


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

    def start(self):
        pass

    def tell(self, *args, **kwargs):
        pass

    def end(self):
        pass


class PackageAnalyzerStub(object):
    def __init__(self, *args, **kwargs):
        """
        `_xml_string` needs to be patched.
        """
        self._xml_string = None
        self.checksum = '5a74db5db860f2f8e3c6a5c64acdbf04'
        self._filename = '/tmp/bla.zip'
        self.meta = {
            'journal_eissn': '1234-1234',
            'journal_pissn': '1234-4321',
            'article_title': 'foo',
            'journal_title': 'Journal Of Oz',
            'issue_year': 2013,
        }

    @property
    def xml(self):
        etree = ElementTree()
        return etree.parse(StringIO(self._xml_string))

    def lock_package(self):
        return None

    def is_valid_package(self):
        return True

    def is_valid_schema(self):
        return True

    def is_valid_meta(self):
        return True

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        return


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
    journal_eissn = '0100-879X'
    journal_pissn = '0100-879X'

    def __init__(self, *args, **kwargs):
        self.id = 1
        self.issue_volume = '31'
        self.issue_number = '1'
        self.issue_suppl_volume = None
        self.issue_suppl_number = None
        self.journal_eissn = '0100-879X'
        self.journal_pissn = '0100-879X'

    def to_dict(self):
        return dict(id=self.id,
                    journal_pissn=self.journal_pissn,
                    journal_eissn=self.journal_eissn,
                    issue_volume=self.issue_volume,
                    issue_number=self.issue_number,
                    issue_suppl_volume=self.issue_suppl_volume,
                    issue_suppl_number=self.issue_suppl_number,
                    related_resources=[('attempts', 'Attempt', [1, 2]),
                                        ('tickets', 'Ticket', [11, 12]),
                        ]
                    )


class ValidationStub(object):
    def __init__(self, *args, **kwargs):
        self.id = 1
        self.status = 1
        self.started_at = '2013-09-18 14:11:04.129956'
        self.finished_at = None
        self.stage = 'Reference'
        self.message = 'Erro no param x...'

    def to_dict(self):
        return dict(id=self.id,
                    message=self.message,
                    stage=self.stage,
                    status=self.status,
                    started_at=str(self.started_at),
                    finished_at=self.finished_at,
                    articlepkg_id=ArticlePkgStub().id,
                    attempt_id=AttemptStub().id)


class AttemptStub(object):
    def __init__(self, *args, **kwargs):
        self.id = 1
        self.is_valid = True
        self.started_at = '2013-09-18 14:11:04.129956'
        self.finished_at = None
        self.filepath = '/tmp/foo/bar.zip'
        self.collection_uri = '/api/v1/collection/xxx/'
        self.package_checksum = 'ol9j27n3f52kne7hbn'
        self.proceed_to_checkout = True,
        self.checkout_started_at = '2011-09-01 14:11:04.129956',
        self.queued_checkout = True,
        self.articlepkg = ArticlePkgStub()

    def to_dict(self):
        return dict(id=self.id,
                    package_checksum=self.package_checksum,
                    articlepkg_id=self.articlepkg.id,
                    started_at=str(self.started_at),
                    finished_at=str(self.finished_at) if self.finished_at else None,
                    collection_uri=self.collection_uri,
                    filepath=self.filepath,
                    is_valid=self.is_valid,
                    )

    def start_validation(self):
        return None

    def end_validation(self):
        return None

    @property
    def analyzer(self):
        return PackageAnalyzerStub()


class CommentStub(object):
    def __init__(self, *args, **kwargs):
        self.id = 1
        self.message = 'Erro no stage xxx'

    def to_dict(self):
        return dict(author='author',
                    message=self.message,
                    date='2013-09-18 14:11:04.129956'
                    )


class TicketStub(object):
    def __init__(self, *args, **kwargs):
        self.id = 1
        self.is_open = True
        self.started_at = '2013-09-18 14:11:04.129956'
        self.finished_at = None
        self.comments = [['Comment', CommentStub().id]]

    def to_dict(self):
        return dict(id=self.id,
                    is_open=self.is_open,
                    started_at=str(self.started_at),
                    finished_at=self.finished_at,
                    comments=self.comments,
                    articlepkg_id=ArticlePkgStub().id)

# ---------------------
# Configuration doubles
# ---------------------
default_config = """
[app]
db_dsn=
socket=balaio.sock
working_dir=/tmp/balaio_wd
log_level=DEBUG
debug_sql=False

[monitor]
watch_path=/vagrant/watch
recursive=True

[manager]
api_key=
api_username=
api_url=http://homolog.manager.scielo.org/api/
notifications=False

[http_server]
ip=0.0.0.0
port=8080

[checkout]
mins_to_wait=1

[static_server]
host=
username=
password=
path=
"""

def ConfigurationStub(config=default_config):
    """Returns a true instance of balaio.utils.Configuration
    with default values.
    """
    cfg = config.strip()
    fp = StringIO(cfg)
    return utils.Configuration(fp)

# --------------------

class ConfigStub(object):
    def get(self, section, option):
        return 'foo'

    def getint(self, section, option):
        return 1

    def items(self):
        return [(None, None)]

    def getboolean(self, section, option):
        return True


class PipeStub(object):
    def __init__(self, data, **kwargs):
        self.data = data

    def __iter__(self):
        for i in self.data:
            yield i


class ObjectStub(object):
    pass


class QueryStub(object):
    def __init__(self, params):
        object.__init__(self)

    def scalar(self):
        return 200

    def limit(self, args):
        o = ObjectStub()
        o.offset = lambda params: []
        if self.found:
            o.offset = lambda params: [self.model(), self.model()]
        return o

    def filter_by(self, **kwargs):
        o = ObjectStub()
        o.limit = self.limit
        o.scalar = self.scalar
        return o

    def get(self, id):
        if not self.found:
            return None
        return self.model()


class DummyRoute:
    """
    Copied from pyramid.tests.test_url.DummyRoute
    """
    pregenerator = None
    name = 'route'
    def __init__(self, result='/1/2/3'):
        self.result = result

    def generate(self, kw):
        self.kw = kw
        return self.result


class DummyRoutesMapper:
    """
    Copied from pyramid.tests.test_url.DummyRoutesMapper
    """
    raise_exc = None
    def __init__(self, route=None, raise_exc=False):
        self.route = route

    def get_route(self, route_name):
        return self.route


class SessionStub(object):
    def __init__(self):
        self._items = []

    def __contains__(self, item):
        return item in self._items

    def add(self, item):
        self._items.append(item)


class SafePackageStub(object):
    def __init__(self, package, working_dir):
        self.primary_path = package
        self.working_dir = working_dir
        self.path = self._gen_safe_path()

    def _gen_safe_path(self):
        basedir = os.path.dirname(self.primary_path)
        fname, fext = os.path.splitext(os.path.basename(self.primary_path))

        packid = 'e7d0213c44ba4ed5adcde9e3fdf62963'
        return os.path.join(self.working_dir, packid+fext)

    @property
    def analyzer(self):
        """
        Returns a PackageAnalyzer instance bound to the package.
        """
        return PackageAnalyzerStub()

    def mark_as_failed(self, silence=False):
        """
        Mark primary path as failed.

        If the target file is gone, the error is logged
        and the exception is silenced.
        """
        try:
            utils.mark_as_failed(self.primary_path)
        except OSError as e:
            logger.debug('The file is gone before marked as failed. %s' % e)
            if not silence: raise

    def mark_as_duplicated(self, silence=False):
        """
        Mark primary path as duplicated.

        If the target file if gone, the error is logged
        and the exception is silenced.
        """
        try:
            utils.mark_as_duplicated(self.primary_path)
        except OSError as e:
            logger.debug('The file is gone before marked as duplicated. %s' % e)
            if not silence: raise


# -------------------
# lib.package doubles
# -------------------
def SafePackageFake(path, working_dir):
    """Produces an instance of `lib.package.SafePackage`
    for tests purposes.

    :param path: absolute path or relative to the `tests` module.
    :param working_dir: same as the original.
    """

    class SafePackageFake(package.SafePackage):
        def _move_to_working_dir(self):
            # act on the original fixture package
            self.path = self.primary_path

    if path.startswith('/'):
        fixture = path
    else:
        fixture = os.path.join(HERE, path)

    safepack = SafePackageFake(fixture, working_dir)
    return safepack


class CheckinReporterFake(package.CheckinReporter):
    """Produces an instance of `lib.package.CheckinReporter`
    for tests purposes.

    The `_messages` attribute can be used to get all messages
    passed to the `tell` method.
    """
    def tell(self, message):
        messages = self.__dict__.setdefault('_messages', [])
        messages.append(message)

# -------------------

#
# Dummy os implementation
#
class DummyProcess(object):
    def read(self):
        return 'active\n'
    def strip(self):
        return 'active'

DummyOs = types.ModuleType('DummyOs')
DummyOs.popen = lambda x: DummyProcess()

