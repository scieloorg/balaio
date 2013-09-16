import os
import hmac
import types
import weakref
import hashlib
import requests
import threading
import logging, logging.handlers
from ConfigParser import SafeConfigParser

try:
    import cPickle as pickle
except ImportError:
    import pickle

logger = logging.getLogger('balaio.utils')
stdout_lock = threading.Lock()
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

    @classmethod
    def from_env(cls):
        try:
            filepath = os.environ['BALAIO_SETTINGS_FILE']
        except KeyError:
            if __debug__:
                # load the test configurations
                cwd = os.path.join(os.path.dirname(__file__))
                filepath = os.path.join(cwd, '..', 'config-test.ini')
            else:
                raise ValueError('missing env variable BALAIO_SETTINGS_FILE')

        return cls.from_file(filepath)

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
        return [(section, dict(self.conf.items(section))) for \
            section in [section for section in self.conf.sections()]]


def make_digest(message, secret='sekretz'):
    """
    Returns a digest for the message based on the given secret

    ``message`` is the file object or byte string to be calculated
    ``secret`` is a shared key used by the hash algorithm
    """
    hash = hmac.new(secret, '', hashlib.sha1)

    if hasattr(message, 'read'):
        while True:
            chunk = message.read(1024)
            if not chunk:
                break
            hash.update(chunk)

    elif isinstance(message, types.StringType):
        hash.update(message)

    else:
        raise TypeError('Unsupported type %s' % type(message))

    return hash.hexdigest()


def make_digest_file(filepath, secret='sekretz'):
    """
    Returns a digest for the filepath based on the given secret

    ``filepath`` is the file to have its bytes calculated
    ``secret`` is a shared key used by the hash algorithm
    """
    with open(filepath, 'rb') as f:
        digest = make_digest(f, secret)

    return digest


def send_message(stream, message, digest, pickle_dep=pickle):
    """
    Serializes the message and flushes it through ``stream``.
    Writes to stream are synchronized in order to keep data
    integrity.

    ``stream`` is a writable socket, pipe, buffer of something like that.
    ``message`` is the object to be dispatched.
    ``digest`` is a callable that generates a hash in order to avoid
    data transmission corruptions.
    """
    if not callable(digest):
        raise ValueError('digest must be callable')

    serialized = pickle_dep.dumps(message, pickle_dep.HIGHEST_PROTOCOL)
    data_digest = digest(serialized)
    header = '%s %s\n' % (data_digest, len(serialized))

    with stdout_lock:
        logger.debug('Stream %s is locked' % stream)
        stream.write(header)
        stream.write(serialized)
        stream.flush()

    logger.debug('Stream %s is unlocked' % stream)
    logger.debug('Message sent with header: %s' % header)


def recv_messages(stream, digest, pickle_dep=pickle):
    """
    Returns an iterator that retrieves messages from the ``stream``
    on its deserialized form.
    When the stream is exhausted the iterator stops, raising
    StopIteration.

    ``stream`` is a readable socket, pipe, buffer of something like that.
    ``digest`` is a callable that generates a hash in order to avoid
    data transmission corruptions.
    """
    if not callable(digest):
        raise ValueError('digest must be callable')

    while True:
        header = stream.readline()

        if not header:
            raise StopIteration()

        in_digest, in_length = header.split(' ')
        in_message = stream.read(int(in_length))

        logger.debug('Received message header: %s message: %s' % (header, in_message))

        if in_digest == digest(in_message):
            yield pickle_dep.loads(in_message)
        else:
            logger.error('Received a corrupted message: %s, %s' % (header, in_message))
            continue


def prefix_file(filename, prefix):
    """
    Renames ``filename`` adding the prefix ``prefix``.
    """
    path, file_or_dir = os.path.split(filename)
    new_filename = os.path.join(path, prefix + file_or_dir)
    os.rename(filename, new_filename)


def mark_as_failed(filename):
    prefix_file(filename, '_failed_')


def setup_logging():
    global has_logger
    # avoid setting up more than once per process
    if has_logger:
        return None
    else:
        rootLogger = logging.getLogger('')
        rootLogger.setLevel(logging.DEBUG)
        socketHandler = logging.handlers.SocketHandler('localhost',
                                                       logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        # don't bother with a formatter, since a socket handler sends the event as
        # an unformatted pickle
        rootLogger.addHandler(socketHandler)
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
    from requests.exceptions import Timeout, RequestException

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
    if not suppl:
        suppl = supplement
    volume_suppl, number_suppl = supplement_type(volume, number, suppl)

    return (volume, volume_suppl, number, number_suppl)
