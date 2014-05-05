#coding: utf-8
import mocker
import unittest
import ConfigParser
from StringIO import StringIO

from balaio.lib import notifier, utils


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


class ZipFilesUtilsTests(unittest.TestCase):

    def setUp(self):
        from StringIO import StringIO
        self.dict_files = {'text': StringIO('Lorem Ipsum é ....'),
                           'img': StringIO('fxx\nfnhjs\nksbhins')}

    def test_if_zip_files_return_file_like_object(self):
        fp = utils.zip_files(self.dict_files)

        self.assertTrue(hasattr(fp, 'read'))

    def test_zip_files_compress_with_deferent_deflate(self):
        import zipfile

        fp = utils.zip_files(self.dict_files, zipfile.ZIP_STORED)

        self.assertTrue(fp)

    def test_zip_files_allow_read_returned_file_like_object(self):
        fp = utils.zip_files(self.dict_files)

        self.assertIsInstance(fp.read(), str)


class GetStaticPathTests(unittest.TestCase):

    def test_get_static_path_with_normal_arq_name(self):
        path = utils.get_static_path('articles', 'aid', 'images.zip')

        self.assertEqual(path, 'articles/aid/images.zip')

    def test_get_static_path_with_level_path(self):
        path = utils.get_static_path("test/articles", 'aid', 'images.zip')

        self.assertEqual(path, 'test/articles/aid/images.zip')

    def test_get_static_path_with_level_aid(self):
        path = utils.get_static_path("articles", 'test/aid', 'images.zip')

        self.assertEqual(path, 'articles/test/aid/images.zip')

    def test_if_get_static_path_with_level_arq_name(self):
        path = utils.get_static_path('articles', 'aid', 'test/images.zip')

        self.assertEqual(path, 'articles/aid/images.zip')

