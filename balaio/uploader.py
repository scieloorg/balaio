# coding:utf-8
import imp
import sys


class Asset(object):
    """
    Remote object allocated in a backend.
    """

    def __init__(self, backend, path):
        """
        :param backend: String indicating the backend to use.
        :param path: Relative path, e.g. u'/journals/pdf/bjmbr-v1n1-01.pdf'.
        """
        self.location = None

    def send(self, fp):
        """
        Upload `fp` to the remote backend.

        :param fp: file-object.
        """


def load_module(name):
    # return the already loaded module, if it is the case.
    try:
        return sys.modules[name]
    except KeyError:
        pass

    file, pathname, description = imp.find_module(name)
    try:
        return imp.load_module(name, file, pathname, description)
    finally:
        if file: file.close()


class BlobBackend(object):
    """
    Base class for remote backends.

    It implements the context manager interface for
    convenience of used.

    If `requires` class attribute is declared with a list
    of valid module names, all modules will be loaded and make
    available by `_modules` class attribute.
    """
    class __metaclass__(type):
        def __new__(cls, name, bases, dict):
            requires = dict.get('requires')
            if requires:
                dict['_modules'] = {name:load_module(name) for name in requires}

            return type.__new__(cls, name, bases, dict)

    def connect(self):
        """
        Establish a connection with the remote host.
        """
        raise NotImplementedError()

    def set_target(self, path):
        """
        Set up the target resource and return a callable representing it.

        :param path: Relative path.
        """
        raise NotImplementedError()

    def cleanup(self):
        """
        Free all system resources.
        """
        raise NotImplementedError()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

