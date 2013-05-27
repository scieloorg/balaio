# coding: utf-8
import ConfigParser

import mocker

import notifier


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
        class Foo(notifier.SingletonMixin):
            pass

        self.assertIs(Foo(), Foo())

    def test_single_int_arg(self):
        class Foo(notifier.SingletonMixin):
            def __init__(self, x):
                self.x = x

        self.assertIs(Foo(2), Foo(2))

    def test_single_int_kwarg(self):
        class Foo(notifier.SingletonMixin):
            def __init__(self, x=None):
                self.x = x

        self.assertIs(Foo(x=2), Foo(x=2))

    def test_multiple_int_arg(self):
        class Foo(notifier.SingletonMixin):
            def __init__(self, x, y):
                self.x = x
                self.y = y

        self.assertIs(Foo(2, 6), Foo(2, 6))

    def test_multiple_int_kwarg(self):
        class Foo(notifier.SingletonMixin):
            def __init__(self, x=None, y=None):
                self.x = x
                self.y = y

        self.assertIs(Foo(x=2, y=6), Foo(x=2, y=6))

    def test_ConfigParser_arg(self):
        class Foo(notifier.SingletonMixin):
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
