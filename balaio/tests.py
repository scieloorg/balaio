# coding: utf-8
import ConfigParser
from StringIO import StringIO

import mocker

import notifier
import utils


class ExtractSettingsFunctionTests(mocker.MockerTestCase):

    def test_simple_extraction(self):
        mock_settings = self.mocker.mock()

        mock_settings.get('manager', 'api_username')
        self.mocker.result('foo_user')

        mock_settings.get('manager', 'api_key')
        self.mocker.result('foo_key')

        mock_settings.get('manager', 'api_url')
        self.mocker.result('http://manager.scielo.org/api/v1/')

        self.mocker.replay()

        self.assertEqual(
            notifier._extract_settings(mock_settings),
            ('http://manager.scielo.org/api/v1/', 'foo_user', 'foo_key'))

    def test_scheme_is_added_if_missing(self):
        mock_settings = self.mocker.mock()

        mock_settings.get('manager', 'api_username')
        self.mocker.result('foo_user')

        mock_settings.get('manager', 'api_key')
        self.mocker.result('foo_key')

        mock_settings.get('manager', 'api_url')
        self.mocker.result('manager.scielo.org/api/v1/')

        self.mocker.replay()

        self.assertEqual(
            notifier._extract_settings(mock_settings),
            ('http://manager.scielo.org/api/v1/', 'foo_user', 'foo_key'))

    def test_ValueError_raised_if_missing_api_username(self):
        mock_settings = self.mocker.mock()

        mock_settings.get('manager', 'api_username')
        self.mocker.throw(ConfigParser.NoOptionError('api_username', 'manager'))

        self.mocker.replay()

        self.assertRaises(
            ValueError,
            lambda: notifier._extract_settings(mock_settings))

    def test_ValueError_raised_if_missing_api_key(self):
        mock_settings = self.mocker.mock()

        mock_settings.get('manager', 'api_username')
        self.mocker.result('foo_user')

        mock_settings.get('manager', 'api_key')
        self.mocker.throw(ConfigParser.NoOptionError('api_key', 'manager'))

        self.mocker.replay()

        self.assertRaises(
            ValueError,
            lambda: notifier._extract_settings(mock_settings))

    def test_ValueError_raised_if_missing_api_url(self):
        mock_settings = self.mocker.mock()

        mock_settings.get('manager', 'api_username')
        self.mocker.result('foo_user')

        mock_settings.get('manager', 'api_key')
        self.mocker.result('foo_key')

        mock_settings.get('manager', 'api_url')
        self.mocker.throw(ConfigParser.NoOptionError('api_url', 'manager'))

        self.mocker.replay()

        self.assertRaises(
            ValueError,
            lambda: notifier._extract_settings(mock_settings))


class SingletonMixinTests(mocker.MockerTestCase):

    def test_without_args(self):
        class Foo(utils.SingletonMixin):
            pass

        self.assertIs(Foo(), Foo())

    def test_single_int_arg(self):
        class Foo(utils.SingletonMixin):
            def __init__(self, x):
                self.x = x

        self.assertIs(Foo(2), Foo(2))

    def test_single_int_kwarg(self):
        class Foo(utils.SingletonMixin):
            def __init__(self, x=None):
                self.x = x

        self.assertIs(Foo(x=2), Foo(x=2))

    def test_multiple_int_arg(self):
        class Foo(utils.SingletonMixin):
            def __init__(self, x, y):
                self.x = x
                self.y = y

        self.assertIs(Foo(2, 6), Foo(2, 6))

    def test_multiple_int_kwarg(self):
        class Foo(utils.SingletonMixin):
            def __init__(self, x=None, y=None):
                self.x = x
                self.y = y

        self.assertIs(Foo(x=2, y=6), Foo(x=2, y=6))

    def test_ConfigParser_arg(self):
        class Foo(utils.SingletonMixin):
            def __init__(self, x):
                self.x = x

        settings = ConfigParser.ConfigParser()
        self.assertIs(
            Foo(settings),
            Foo(settings)
        )


class RequestTests(mocker.MockerTestCase):

    def test_request_is_singleton(self):
        self.assertIs(
            notifier.Request('http://manager.scielo.org/', 'foo_user', 'foo_key'),
            notifier.Request('http://manager.scielo.org/', 'foo_user', 'foo_key')
        )

    def test_new_http_request_adds_authorization_header(self):

        req = notifier.Request('http://manager.scielo.org/', 'foo_user', 'foo_key')

        self.assertTrue(
            req._new_http_request().has_header('Http_authorization')
        )
        self.assertEqual(
            req._new_http_request().get_header('Http_authorization'),
            'ApiKey foo_user:foo_key'
        )

    def test_new_http_request_sets_url(self):
        req = notifier.Request('http://manager.scielo.org/', 'foo_user', 'foo_key')

        self.assertEqual(
            req._new_http_request().get_full_url(),
            'http://manager.scielo.org/'
        )


class NotifierTests(mocker.MockerTestCase):

    def test_request_is_singleton(self):
        mock_request = self.mocker.mock(notifier.Request)
        mock_settings = self.mocker.mock()

        mock_settings.get('manager', 'api_username')
        self.mocker.result('foo_user')
        self.mocker.count(2)

        mock_settings.get('manager', 'api_key')
        self.mocker.result('foo_key')
        self.mocker.count(2)

        mock_settings.get('manager', 'api_url')
        self.mocker.result('manager.scielo.org/api/v1/')
        self.mocker.count(2)

        self.mocker.replay()

        self.assertIs(
            notifier.Notifier(mock_settings, mock_request),
            notifier.Notifier(mock_settings, mock_request)
        )


class ValidadeNotificationMessageFunctionTests(mocker.MockerTestCase):

    def test_valid_msg(self):
        fields = ('checkin_id', 'collection_uri', 'article_title')
        message = {
            'checkin_id': 'aaaa',
            'collection_uri': '/api/v1/collections/1/',
            'article_title': 'Foo Bar',
        }

        self.assertTrue(
            notifier.validate_notification_message(message, fields))

    def test_invalid_msg(self):
        fields = ('checkin_id', 'collection_uri')
        message = {
            'checkin_id': 'aaaa',
            'collection_uri': '/api/v1/collections/1/',
            'article_title': 'Foo Bar',
        }

        self.assertFalse(
            notifier.validate_notification_message(message, fields))


class ConfigurationTests(mocker.MockerTestCase):

    def _make_fp(self):
        mock_fp = self.mocker.mock()

        mock_fp.name
        self.mocker.result('settings.ini')

        mock_fp.readline()
        self.mocker.result('[app]')

        mock_fp.readline()
        self.mocker.result('status = True')

        mock_fp.readline()
        self.mocker.result('')

        self.mocker.replay()

        return mock_fp

    def test_fp(self):
        mock_fp = self._make_fp()
        conf = utils.Configuration(mock_fp)
        self.assertEqual(conf.get('app', 'status'), 'True')

    def test_non_existing_option_raises_ConfigParser_NoOptionError(self):
        mock_fp = self._make_fp()
        conf = utils.Configuration(mock_fp)
        self.assertRaises(
            ConfigParser.NoOptionError,
            lambda: conf.get('app', 'missing'))

    def test_non_existing_section_raises_ConfigParser_NoSectionError(self):
        mock_fp = self._make_fp()
        conf = utils.Configuration(mock_fp)
        self.assertRaises(
            ConfigParser.NoSectionError,
            lambda: conf.get('missing', 'status'))


class MakeDigestFunctionTests(mocker.MockerTestCase):
    """
    blackbox tests approach.
    """
    def test_digests_are_determinist(self):
        self.assertEqual(
            utils.make_digest('foo'),
            utils.make_digest('foo')
        )

    def test_digests_are_sensible_to_secret_keys(self):
        self.assertNotEqual(
            utils.make_digest('foo'),
            utils.make_digest('foo', secret='bar')
        )

    def test_digests_have_no_newline_char(self):
        self.assertFalse('\n' in utils.make_digest('foo'))

    def test_invalid_messages_raise_TypeError(self):
        self.assertRaises(
            TypeError,
            lambda: utils.make_digest(object()))

    def test_digests_for_file_objects(self):
        file1 = StringIO('Some content')
        file2 = file1.getvalue()

        self.assertEqual(
            utils.make_digest(file1),
            utils.make_digest(file2)
        )

    def test_digests_for_file_obj_are_sensible_to_secret_keys(self):
        file1 = StringIO('Some content')
        file2 = file1.getvalue()

        self.assertNotEqual(
            utils.make_digest(file1),
            utils.make_digest(file2, secret='bar')
        )


class SendMessageFunctionTests(mocker.MockerTestCase):

    def test_stream_is_flushed(self):
        mock_stream = self.mocker.mock()

        mock_stream.write(mocker.ANY)
        self.mocker.result(None)
        self.mocker.count(2)

        mock_stream.flush()
        self.mocker.result(None)

        self.mocker.replay()

        self.assertIsNone(
            utils.send_message(mock_stream, 'message', utils.make_digest))

    def test_serialized_data_digest_in_header(self):
        """
        The data header is formed by:
        <serialized data digest> <serialized data length>\n
        """
        mock_digest = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')
        self.mocker.replay()

        stream = StringIO()

        utils.send_message(stream, 'message', mock_digest)
        self.assertEqual(
            stream.getvalue().split('\n')[0].split(' ')[0],
            'e5fcf4f4606df6368779205e29b22e5851355de3'
        )

    def test_serialized_data_length_in_header(self):
        """
        The data header is formed by:
        <serialized data digest> <serialized data length>\n
        """
        mock_digest = self.mocker.mock()
        mock_pickle = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')

        mock_pickle.HIGHEST_PROTOCOL
        self.mocker.result('foo')

        mock_pickle.dumps(mocker.ANY, mocker.ANY)
        self.mocker.result('serialized-data-byte-string')

        self.mocker.replay()

        stream = StringIO()

        utils.send_message(stream, 'message', mock_digest, pickle_dep=mock_pickle)

        self.assertEqual(
            int(stream.getvalue().split('\n')[0].split(' ')[1]),
            len('serialized-data-byte-string')
        )


class RecvMessageFunctionTests(mocker.MockerTestCase):
    serialized_message = 'e5fcf4f4606df6368779205e29b22e5851355de3 14\n\x80\x02U\x07messageq\x01.'

    def test_valid_data_is_deserialized(self):
        mock_digest = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')
        self.mocker.replay()

        in_stream = StringIO(self.serialized_message)
        messages = utils.recv_messages(in_stream, mock_digest)

        self.assertEqual(messages.next(), 'message')

    def test_corrupted_data_is_bypassed(self):
        mock_digest = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3XXXXX')
        self.mocker.replay()

        in_stream = StringIO(self.serialized_message)
        messages = utils.recv_messages(in_stream, mock_digest)

        self.assertRaises(StopIteration, lambda: messages.next())

    def test_raises_StopIteration_while_the_stream_is_exhausted(self):
        in_stream = StringIO()
        messages = utils.recv_messages(in_stream, utils.make_digest)

        self.assertRaises(StopIteration, lambda: messages.next())
