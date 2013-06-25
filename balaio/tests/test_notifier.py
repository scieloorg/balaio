import mocker

from balaio import notifier


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
