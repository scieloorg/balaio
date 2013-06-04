# coding: utf-8
import ConfigParser
import urllib2
import urllib

from .utils import SingletonMixin, Configuration

# the environment variable is not set under tests
if __debug__:
    config = None
else:
    config = Configuration.from_env()

CHECKIN_MESSAGE_FIELDS = ('checkin_id', 'collection_uri', 'article_title',
    'journal_title', 'issue_label', 'pkgmeta_filename', 'pkgmeta_md5',
    'pkgmeta_filesize', 'pkgmeta_filecount', 'pkgmeta_submitter')


def _extract_settings(settings):
    """
    Returns a tuple with url, username and apikey values.
    """
    try:
        api_username = settings.get('manager', 'api_username')
        api_key = settings.get('manager', 'api_key')
        api_url = settings.get('manager', 'api_url')
    except (ConfigParser.NoSectionError,
            ConfigParser.NoOptionError):
        raise ValueError('Missing configuration: manager')

    url = api_url
    if not url.startswith('http://'):
        url = 'http://' + url

    return (url, api_username, api_key)


class Request(SingletonMixin):

    def __init__(self,
                 url,
                 api_username,
                 api_key,
                 urlencode_dep=urllib.urlencode,
                 urllib_dep=urllib2):
        """
        ``url``
        ``api_username``
        ``api_key``
        """
        self._urlencode = urlencode_dep
        self._urllib2 = urllib_dep

        self.url = url
        self.username = api_username
        self.apikey = api_key

    def _new_http_request(self):
        request = self._urllib2.Request(self.url)
        request.add_header(
            'HTTP_AUTHORIZATION',
            'ApiKey {0}:{1}'.format(self.username, self.apikey))

        return request

    def _prepare_data(self, data):
        return self._urlencode(data)

    def post(self, data):
        """
        Assembles an HTTP POST and returns a file-object.

        ``data`` is a mapping.
        """
        req = self._new_http_request()
        req.add_data(self._prepare_data(data))

        return self._urllib2.urlopen(req)


class Notifier(SingletonMixin):

    def __init__(self, settings=config, request_dep=Request):
        """
        ``settings`` is an instance of ConfigParser.ConfigParser.
        """
        assert isinstance(request_dep, Request)

        self._request = request_dep
        self._url, self._username, self._apikey = _extract_settings(settings)

    def _prepare_url(self, endpoint):
        return '%s/%s/' % (self._url, endpoint)

    def _submit(self, endpoint, data):
        """
        Submits json-encoded data to the given endpoint.

        ``endpoint`` is a string representing an available
        endpoint at SciELO Manager.
        See: http://manager.scielo.org/api/v1/
        ``data`` is a mapping in the format expected
        by the remote endpoint.
        """
        full_url = self._prepare_url(endpoint)
        req = self._request(full_url, self._username, self._apikey)
        req.post(data)

    def checkin(self, message):
        """
        Sends a checkin notification event to a remote endpoint.

        ``message`` is a mapping with the fields listed at
        CHECKIN_MESSAGE_FIELDS.
        """
        if not validate_notification_message(message, CHECKIN_MESSAGE_FIELDS):
            raise ValueError('invalid message')

        self._submit('articlepkg_checkins', message)

    def validation_event(self, message):
        """
        Sends a validation checkpoint notification event to a
        remote endpoint.

        ``message`` is a mapping with the fields listed at
        VALIDATION_MESSAGE_FIELDS.
        """


def validate_notification_message(message, fields):
    """
    ``message`` is what needs to be validaded.
    ``fields`` is a tuple of field names that need to be present.
    """
    fields_set = set(fields)
    msg_fields_set = set(message.keys())

    return fields_set == msg_fields_set
