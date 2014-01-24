# coding:utf-8
import imp
import sys

from balaio import utils


class Asset(object):
    """
    Remote object allocated in a backend.
    """
    _backends = {}

    def __init__(self, backend, path, **kwargs):
        """
        :param backend: String indicating the backend to use.
        :param path: Relative path, e.g. u'/journals/pdf/bjmbr-v1n1-01.pdf'.
        """
        self.location = None
        self.path = path
        try:
            self.backend = self._backends[backend](**kwargs)
        except KeyError:
            raise ValueError(u'Unknown backend %s' % backend)

    def send(self, fp):
        """
        Upload `fp` to the remote backend.

        :param fp: file-object.
        """
        with self.backend as backend:
            self.location = backend.send(fp, self.path)

    @classmethod
    def register_backend(cls, name, backend):
        """
        Register only enabled backends to be used by instances of Asset.

        :param name: The name of the backend.
        :param backend: Backend class object.
        """
        if backend.enabled():
            cls._backends[name] = backend


def load_module(name):
    """
    Try to load the module known by `name`.

    If the module is not found, `None` is returned.
    :param name: is a string of the module name.
    """
    # return the already loaded module, if it is the case.
    try:
        return sys.modules[name]
    except KeyError:
        pass

    try:
        file, pathname, description = imp.find_module(name)
    except ImportError:
        return None

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
                dict['_modules'] = {mod_name:load_module(mod_name) for mod_name in requires}
            else:
                dict['_modules'] = {}

            instance = type.__new__(cls, name, bases, dict)

            # Make the backend available for Asset instances
            Asset.register_backend(name, instance)

            # Decorate __init__ to make sure the backend is enabled
            # during instantiation.
            def init_wrapper(method):
                def assert_enabled(*args, **kwargs):
                    if not instance.enabled():
                        deps = ', '.join([k for k, v in instance._modules.items() if not v])
                        raise ValueError('Missing dependencies: %s' % deps)
                    else:
                        method(*args, **kwargs)
                return assert_enabled

            instance.__init__ = init_wrapper(instance.__init__)
            return instance


    def connect(self):
        """
        Establish a connection with the remote host.
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

    @classmethod
    def enabled(cls):
        """
        If all required modules are available.
        """
        return all(cls._modules.values())


class StaticScieloBackend(BlobBackend):
    """
    Stores data in static.scielo.org.
    """
    requires = ['paramiko']
    base_url = u'http://static.scielo.org/'

    def __init__(self, username, password, basepath, host=None, port=None):
        self.username = username
        self.password = password
        self.basepath = basepath
        self.host = host or u'static.scielo.org'
        self.port = port or 22
        self.sftp = None

    def connect(self):
        paramiko = self._modules['paramiko']

        self.transport = paramiko.Transport((self.host, self.port))

        #raises paramiko.SSHException
        self.transport.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

        # changes the current working directory to basepath
        self.sftp.chdir(self.basepath)

    def cleanup(self):
        """
        Close the transport layer and rebind the sftp object.
        """
        self.transport.close()
        self.sftp = None

    def send(self, fp, path):
        """
        :param fp:
        :param path: Text string like /articles/foo/foo.pdf
        """
        # get the full-qualified path, i.e:
        # '/art/foo.pdf' => '/var/static/art/foo.pdf'
        fqpath = self._get_fqpath(path)

        # make sure all expected parent directories exists
        # before start transfering `fp`.
        self._ensure_parent_dir(fqpath)

        self.sftp.putfo(fp, fqpath, confirm=True)

        return self._get_resource_uri(path)

    def _get_fqpath(self, path):
        """
        Get the full-qualified path for `path`.
        """
        s_basepath = self.basepath.split(u'/')
        s_path = path.split(u'/')

        segments = [seg for seg in (s_basepath + s_path) if seg]
        fqpath = u'/'.join(segments)

        if not fqpath.startswith(u'/'):
            fqpath = u'/' + fqpath

        return fqpath

    def _ensure_parent_dir(self, fqpath):
        """
        Ensure all parent dirs of `fqpath` exists.

        TODO: This method should be optimized for cases where the
        basedir already exists.
        """
        if fqpath.startswith('/'):
            fqpath = fqpath[1:]

        # only dirnames are required
        splitted_remote_path = fqpath.split('/')[:-1]

        current_path = u'/'
        for path_segment in splitted_remote_path:
            current_path += path_segment
            try:
                self.sftp.mkdir(current_path)
            except IOError:
                pass #assuming the directory already exists
            current_path += '/'

    def _get_resource_uri(self, path):
        """
        Produces a publicly accessible URL do `path`.
        """
        base_url = self.base_url
        if not base_url.endswith(u'/'):
            base_url += u'/'

        if path.startswith(u'/'):
            path = path[1:]

        return base_url + path

