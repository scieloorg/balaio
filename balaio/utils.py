import os
from ConfigParser import SafeConfigParser
import weakref
import hmac
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle
import threading


stdout_lock = threading.Lock()


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
        if __debug__:
            # load the test configurations
            cwd = os.path.join(os.path.dirname(__file__))
            filepath = os.path.join(cwd, '..', 'config-test.ini')
        else:
            try:
                filepath = os.environ['BALAIO_SETTINGS_FILE']
            except KeyError:
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


def make_digest(message, secret='sekretz'):
    """
    Returns a digest for the message based on the given secret

    ``message`` is the byte string to be calculated
    ``secret`` is a shared key used by the hash algorithm
    """
    hash = hmac.new(secret,
                    message,
                    hashlib.sha1)
    return hash.hexdigest()


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
        stream.write(header)
        stream.write(serialized)
        stream.flush()


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

        if in_digest == digest(in_message):
            yield pickle_dep.loads(in_message)
        else:
            # log the failure
            continue
