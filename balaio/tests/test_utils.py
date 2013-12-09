import mocker
import unittest
import ConfigParser
from StringIO import StringIO

from balaio import notifier
from balaio import utils


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
    sock_path = 'balaio-tests.sock'

    def tearDown(self):
        utils.remove_unix_socket(self.sock_path)

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

    def test_socket_stream_support(self):
        import socket
        sock_one, sock_two = socket.socketpair()

        mock_digest = self.mocker.mock()
        mock_pickle = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')

        mock_pickle.HIGHEST_PROTOCOL
        self.mocker.result('foo')

        mock_pickle.dumps(mocker.ANY, mocker.ANY)
        self.mocker.result('serialized-data-byte-string')

        self.mocker.replay()

        utils.send_message(sock_one, 'message', mock_digest, pickle_dep=mock_pickle)
        self.assertEqual(
            int(sock_two.recv(1024).split('\n')[0].split(' ')[1]),
            len('serialized-data-byte-string')
        )

    def test_unix_socket_stream_support(self):
        import socket

        mock_digest = self.mocker.mock()
        mock_pickle = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')

        mock_pickle.HIGHEST_PROTOCOL
        self.mocker.result('foo')

        mock_pickle.dumps(mocker.ANY, mocker.ANY)
        self.mocker.result('serialized-data-byte-string')

        self.mocker.replay()

        out_stream = utils.get_readable_socket(self.sock_path)
        out_stream.setblocking(1)  # avoid blocking
        in_stream = utils.get_writable_socket(self.sock_path)

        utils.send_message(in_stream, 'message', mock_digest, pickle_dep=mock_pickle)
        conn, _ = out_stream.accept()
        self.assertEqual(
            int(conn.recv(1024).split('\n')[0].split(' ')[1]),
            len('serialized-data-byte-string')
        )


class RecvMessageFunctionTests(mocker.MockerTestCase):
    serialized_message = 'e5fcf4f4606df6368779205e29b22e5851355de3 14\n\x80\x02U\x07messageq\x01.'
    sock_path = 'balaio-tests.sock'

    def tearDown(self):
        utils.remove_unix_socket(self.sock_path)

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

    def test_socket_stream_support(self):
        import socket
        mock_digest = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')
        self.mocker.replay()

        in_stream, out_stream = socket.socketpair()
        in_stream.sendall(self.serialized_message)
        messages = utils.recv_messages(out_stream, mock_digest)

        self.assertEqual(messages.next(), 'message')

    def test_unix_socket_stream_support(self):
        mock_digest = self.mocker.mock()
        mock_digest(mocker.ANY)
        self.mocker.result('e5fcf4f4606df6368779205e29b22e5851355de3')
        self.mocker.replay()

        out_stream = utils.get_readable_socket(self.sock_path)
        in_stream = utils.get_writable_socket(self.sock_path)

        in_stream.sendall(self.serialized_message)
        messages = utils.recv_messages(out_stream, mock_digest)

        self.assertEqual(messages.next(), 'message')


class ISSNFunctionsTest(unittest.TestCase):

    def test_calc_check_digit_issn_with_valid_ISSN(self):
        issn = u'0102-3306'

        self.assertEqual(utils.calc_check_digit_issn(issn), issn[-1])

    def test_calc_check_digit_issn_with_invalid_ISSN(self):
        issn = u'2179-9752'

        self.assertNotEqual(utils.calc_check_digit_issn(issn), issn[-1])

    def test_calc_check_digit_issn_with_check_digit_zero(self):
        issn = u'0102-8650'

        self.assertEqual(utils.calc_check_digit_issn(issn), issn[-1])

    def test_calc_check_digit_issn_with_check_digit_X(self):
        issn = u'2179-975X'

        self.assertEqual(utils.calc_check_digit_issn(issn), issn[-1])

    def test_validate_issn_with_ISSN_as_Number(self):
        issn = 21799754

        self.assertRaises(TypeError, lambda: utils.validate_issn(issn))

    def test_validate_issn_with_no_well_format_without_hyphen(self):
        issn = u'217a9754'

        self.assertRaises(ValueError, lambda: utils.validate_issn(issn))

    def test_validate_issn_with_no_well_format_with_hyphen(self):
        issn = u'2-1799754'

        self.assertRaises(ValueError, lambda: utils.validate_issn(issn))

    def test_validate_issn_with_size_smaller_than_eight(self):
        issn = u'2179-975'

        self.assertRaises(ValueError, lambda: utils.validate_issn(issn))

    def test_validate_issn_with_size_greater_than_eight(self):
        issn = u'2179-975123'

        self.assertRaises(ValueError, lambda: utils.validate_issn(issn))

    def test_validate_issn_with_no_numerical_issn(self):
        issn = u'abcd-fghi'

        self.assertRaises(ValueError, lambda: utils.validate_issn(issn))

    def test_is_valid_issn_with_valid_issn(self):
        issn = u'2179-975X'

        self.assertTrue(utils.is_valid_issn(issn))

    def test_is_valid_issn_with_invalid_issn(self):
        issn = u'2179-9753'

        self.assertFalse(utils.is_valid_issn(issn))


class DOIFunctionsTests(mocker.MockerTestCase):

    def test_valid_doi_status_200(self):
        mock_is_valid = self.mocker.mock()

        mock_is_valid.status_code
        self.mocker.result(200)

        requests = self.mocker.replace("requests.get")
        requests('http://dx.doi.org/10.1590/S2179-975X2012005000031', timeout=2.5)
        self.mocker.result(mock_is_valid)

        self.mocker.replay()

        self.assertTrue(utils.is_valid_doi('10.1590/S2179-975X2012005000031'))

    def test_valid_doi_status_404(self):
        mock_is_valid = self.mocker.mock()

        mock_is_valid.status_code
        self.mocker.result(404)

        requests = self.mocker.replace("requests.get")
        requests('http://dx.doi.org/10.1590/S2179-975X2012005XXXX', timeout=2.5)
        self.mocker.result(mock_is_valid)

        self.mocker.replay()

        self.assertFalse(utils.is_valid_doi('10.1590/S2179-975X2012005XXXX'))

    def test_valid_doi_status_500(self):
        mock_is_valid = self.mocker.mock()

        mock_is_valid.status_code
        self.mocker.result(500)

        requests = self.mocker.replace("requests.get")
        requests('http://dx.doi.org/10.1590/S2179-975X2012005XXXX', timeout=2.5)
        self.mocker.result(mock_is_valid)

        self.mocker.replay()

        self.assertFalse(utils.is_valid_doi('10.1590/S2179-975X2012005XXXX'))

    def test_valid_doi_with_any_network_problem(self):
        import requests

        _requests = self.mocker.replace("requests.get")
        _requests('http://dx.doi.org/10.1590/S2179-975X2012005000031', timeout=2.5)
        self.mocker.throw(requests.exceptions.RequestException)

        self.mocker.replay()

        self.assertRaises(requests.exceptions.RequestException, lambda: utils.is_valid_doi('10.1590/S2179-975X2012005000031'))

    def test_valid_doi_with_request_timeout(self):
        import requests

        _requests = self.mocker.replace("requests.get")
        _requests('http://dx.doi.org/10.1590/S2179-975X2012005000031', timeout=2.5)
        self.mocker.throw(requests.exceptions.Timeout)

        self.mocker.replay()

        self.assertRaises(requests.exceptions.Timeout, lambda: utils.is_valid_doi('10.1590/S2179-975X2012005000031'))


class ParseIssueTagTest(unittest.TestCase):

    def test_issue_tag_content_is_empty(self):
        self.assertEqual(utils.parse_issue_tag(''), (None, None, None))

    def test_issue_tag_content_is_a_issue_number_only(self):
        self.assertEqual(utils.parse_issue_tag('3A'), ('3A', None, None))

    def test_issue_tag_content_is_suppl_only(self):
        self.assertEqual(utils.parse_issue_tag('Supplement'), (None, 'Supplement', None))

    def test_issue_tag_content_is_a_issue_number_with_supplement(self):
        self.assertEqual(utils.parse_issue_tag('3 Supl'), ('3', 'Supl', None))

    def test_issue_tag_content_is_a_issue_number_with_supplement_number(self):
        self.assertEqual(utils.parse_issue_tag('3 Supl 1'), ('3', 'Supl', '1'))

    def test_issue_tag_content_is_supplement_number(self):
        self.assertEqual(utils.parse_issue_tag('Supl 1'), (None, 'Supl', '1'))


class SupplementTypeTests(unittest.TestCase):

    def test_supplement_type_of_no_supplements(self):
        self.assertEqual(utils.supplement_type('31', '1', None), (None, None))

    def test_supplement_type_of_suppl_number(self):
        self.assertEqual(utils.supplement_type('31', '1', '2'), (None, '2'))

    def test_supplement_type_of_suppl_volume(self):
        self.assertEqual(utils.supplement_type('31', None, '2'), ('2', None))


class IssueIdentificationTests(unittest.TestCase):

    def test_issue_identification_volume(self):
        self.assertEqual(utils.issue_identification('31', None, None), ('31', None, None, None))

    def test_issue_identification_number(self):
        self.assertEqual(utils.issue_identification(None, '1', None), (None, None, '1', None))

    def test_issue_identification_volume_and_number(self):
        self.assertEqual(utils.issue_identification('31', '1', None), ('31', None, '1', None))

    def test_issue_identification_volume_number_and_suppl(self):
        self.assertEqual(utils.issue_identification('31', '1', '2'), ('31', None, '1', '2'))

    def test_issue_identification_volume_and_suppl(self):
        self.assertEqual(utils.issue_identification('31', None, '2'), ('31', '2', None, None))

    def test_issue_identification_number_and_suppl(self):
        self.assertEqual(utils.issue_identification(None, '4', '2'), (None, None, '4', '2'))

    def test_number_is_lstripped(self):
        self.assertEqual(utils.issue_identification(None, '01', None), (None, None, '1', None))

    def test_volume_is_lstripped(self):
        self.assertEqual(utils.issue_identification('031', None, None), ('31', None, None, None))


class RemoveUnixSocketTests(unittest.TestCase):

    def test_remove_socket(self):
        import tempfile, os
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        file_name = tmp_file.name
        tmp_file.close()

        utils.remove_unix_socket(file_name)

        self.assertFalse(os.path.exists(file_name))


class FileLikeSocketAdaperTests(unittest.TestCase):

    def setUp(self):
        import socket
        self.sock_one, self.sock_two = socket.socketpair()

    def test_readline(self):
        # without the last \n it will block forever
        self.sock_one.sendall('only fluids, the doc said.\ngimme a beer!\n')

        fsock = utils.FileLikeSocket(self.sock_two)
        self.assertEquals(fsock.readline(), 'only fluids, the doc said.')
        self.assertEquals(fsock.readline(), 'gimme a beer!')

    def test_read(self):
        self.sock_one.sendall('only fluids, the doc said.\ngimme a beer!\n')

        fsock = utils.FileLikeSocket(self.sock_two)
        self.assertEquals(fsock.read(4), 'only')

    def test_write(self):
        fsock = utils.FileLikeSocket(self.sock_one)
        fsock.write('foo')

        self.assertEquals(self.sock_two.recv(1024), 'foo')

    def flush(self):
        # does nothing, but must be present
        fsock = utils.FileLikeSocket(self.sock_one)
        self.assertTrue(hasattr(fsock, 'flush'))

