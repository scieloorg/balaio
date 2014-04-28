import os
import weakref
import requests
import zipfile
from StringIO import StringIO
import logging, logging.handlers
from ConfigParser import SafeConfigParser

from requests.exceptions import Timeout, RequestException


logger = logging.getLogger('balaio.utils')

# flag to indicate if the process have
# already defined a logger handler.
has_logger = False


class SingletonMixin(object):
    """
    Adds a singleton behaviour to an existing class.

    weakrefs are used in order to keep a low memory footprint.
    As a result, args and kwargs passed to classes initializers
    must be of weakly refereable types.
    """
    _instances = weakref.WeakValueDictionary()

    def __new__(cls, *args, **kwargs):
        key = (cls, args, tuple(kwargs.items()))

        if key in cls._instances:
            return cls._instances[key]

        new_instance = super(type(cls), cls).__new__(cls, *args, **kwargs)
        cls._instances[key] = new_instance

        return new_instance


class Configuration(SingletonMixin):
    """
    Acts as a proxy to the ConfigParser module
    """
    def __init__(self, fp, parser_dep=SafeConfigParser):
        self.conf = parser_dep()
        self.conf.readfp(fp)
        self._fp = fp

    @property
    def fp(self):
        # Workaround to make the fp readable indefinitely.
        # But this code has serious problems on concurrent environments.
        self._fp.seek(0)
        return self._fp

    @classmethod
    def from_file(cls, filepath):
        """
        Returns an instance of Configuration

        ``filepath`` is a text string.
        """
        fp = open(filepath, 'rb')
        return cls(fp)

    def __getattr__(self, attr):
        return getattr(self.conf, attr)

    def items(self):
        """Settings as key-value pair.
        """
        return [(section, dict(self.conf.items(section, raw=True))) for \
            section in [section for section in self.conf.sections()]]


def balaio_config_from_env():
    """
    Returns an instance of Configuration.
    """
    try:
        filepath = os.environ['BALAIO_SETTINGS_FILE']
    except KeyError:
        raise ValueError('missing env variable BALAIO_SETTINGS_FILE')

    return Configuration.from_file(filepath)


def alembic_config_from_env():
    """
    Returns an instance of Configuration.

    Alembic is a DB migrations system for SqlAlchemy.
    """
    try:
        filepath = os.environ['BALAIO_ALEMBIC_SETTINGS_FILE']
    except KeyError:
        raise ValueError('missing env variable BALAIO_ALEMBIC_SETTINGS_FILE')

    return Configuration.from_file(filepath)


def prefix_file(filename, prefix):
    """
    Renames ``filename`` adding the prefix ``prefix``.
    """
    path, file_or_dir = os.path.split(filename)
    new_filename = os.path.join(path, prefix + file_or_dir)
    os.rename(filename, new_filename)


def mark_as_failed(filename):
    prefix_file(filename, '_failed_')


def mark_as_duplicated(filename):
    prefix_file(filename, '_duplicated_')


def setup_logging(config):
    global has_logger

    # avoid setting up more than once per process
    if has_logger:
        return None
    else:
        from logging.config import fileConfig
        fileConfig(config.fp)

        has_logger = True


def normalize_data(data):
    """
    Normalize the ``data`` param converting to uppercase and clean spaces

    Convert this: ' This is     a test for something good      '
    To this: 'THIS IS A TEST FOR SOMETHING GOOD'

    """
    return ' '.join(data.upper().split())


def is_valid_doi(doi):
    """
    Verify if the DOI is valid for CrossRef
    Validate URL: ``http://dx.doi.org/<DOI>``
    Raise any connection and timeout error
    """

    try:
        req = requests.get('http://dx.doi.org/%s' % doi, timeout=2.5)
    except (Timeout, RequestException) as e:
        logger.error('Can not validate doi: ' + str(e))
        raise
    else:
        return req.status_code == 200


def validate_issn(issn):
    """
    This function analyze the ISSN:
        - Verify if it`s a string
        - Verify the length
        - Verify the format: ``0102-6720``
        - Return issn if it`s valid
    """

    if not isinstance(issn, basestring):
        raise TypeError('Invalid type')
    if len(issn) != 9:
        raise ValueError('Invalid length')
    if not '-' in issn:
        raise ValueError('Invalid format')
    if calc_check_digit_issn(issn) != issn[-1]:
        raise ValueError('Invaid ISSN')

    return issn


def calc_check_digit_issn(issn):
    """
    Calculate the check digit of the ISSN

    https://en.wikipedia.org/wiki/International_Standard_Serial_Number
    """

    total = 0
    lissn = list(issn.replace('-', ''))

    for i, v in enumerate(lissn[:-1]):
        total = total + ((8-i) * int(v))

    remainder = total % 11

    if not remainder:
        check_digit = 0
    else:
        check_digit = 11 - remainder

    return 'X' if check_digit == 10 else str(check_digit)


def is_valid_issn(issn):
    """
    Return True if valid, otherwise False.
    """
    try:
        return bool(validate_issn(issn))
    except (ValueError, TypeError):
        return False


def parse_issue_tag(issue_tag_content):
    """
    Parse issue tag content and returns issue number, label and supplement

    :returns: (number, label, suppl)
    """
    # <issue> contents:
    # <issue>2</issue>
    # <issue>Suppl</issue>
    # <issue>3 Suppl 1</issue>
    # <issue>Suppl 1</issue>
    number, suppl_label, suppl = [None, None, None]
    if issue_tag_content:
        lower_issue = issue_tag_content.lower()
        if 'sup' in lower_issue:
            # number
            number = lower_issue[0:lower_issue.find('sup')].strip()
            if number == '':
                number = None

            # supplement label
            suppl_label = issue_tag_content[lower_issue.find('sup'):]
            if ' ' in suppl_label:
                suppl_label = suppl_label[0:suppl_label.find(' ')]

            # supplement
            suppl = issue_tag_content[issue_tag_content.find(suppl_label) + len(suppl_label):].strip()
            if suppl == '':
                suppl = None
        else:
            number = issue_tag_content

    return (number, suppl_label, suppl)


def supplement_type(volume, number, suppl):
    """
    Identifies the type of the supplement: volume or number

    :param volume: issue volume
    :param number: issue number
    :param suppl: 1, Suppl, None
    :returns: (issue_suppl_volume, issue_suppl_number)
    """
    issue_suppl_volume = None
    issue_suppl_number = None

    if number:
        issue_suppl_number = suppl
    else:
        issue_suppl_volume = suppl
    return (issue_suppl_volume, issue_suppl_number)


def issue_identification(volume, number, supplement):
    """
    Identifies the elements which forms a issue: volume, number, supplement volume, supplement number

    :param volume: issue volume
    :param number: issue number
    :param supplement: 1, Suppl, None
    :returns: (volume, volume_suppl, number, number_suppl)
    """
    # issue can have contents like: 2, Suppl, 3 Suppl 1, Suppl 1
    number, label, suppl = parse_issue_tag(number)
    if label and not suppl:
        suppl = label
    else:
        suppl = supplement
    volume_suppl, number_suppl = supplement_type(volume, number, suppl)

    if volume is not None:
        volume = volume.lstrip('0')

    if number is not None:
        number = number.lstrip('0')

    return (volume, volume_suppl, number, number_suppl)


def zip_files(dict_files, compression=zipfile.ZIP_DEFLATED):
    """
    Compact dict itens passed by parameter and return a file-like object

    :param dict_files: ``key``: name of file, ``value``: bytes
    """
    in_memory = StringIO()

    with zipfile.ZipFile(in_memory, 'w', compression) as zf:
        for fname, fp in dict_files.iteritems():
            zf.writestr(fname, fp.read())

    zf.close()

    in_memory.seek(0)

    return in_memory


def get_static_path(path, aid, filename):
    """
    Produces the path to the static file based on file ``path``, ``name`` and ``aid``
    :param path: path to the backend
    :param aid: aid (article identify)
    :param filename: name of the file
    """
    return os.path.join(path, aid, os.path.basename(filename))

