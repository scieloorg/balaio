import mocker
import unittest
from xml.etree.ElementTree import ElementTree
from StringIO import StringIO


class FundingCheckingPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import FundingCheckingPipe
        return FundingCheckingPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root><journal-title>Revista Brasileira ...</journal-title></root>'):

        etree = ElementTree()
        xml = etree.parse(StringIO(xml_string))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        return (attempt, pkg_analyzer)

    def _validate(self, xml_string):
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        data = self._make_data(xml_string)
        self.mocker.replay()

        pipe = self._make_pipe(data, mock_manager, mock_notifier)
        return pipe.validate(data[1])

    def test_no_funding_group_and_no_ack(self):
        expected = ['w', 'no funding-group and no ack']

        self.assertEquals(
            expected,
            self._validate('<root></root>'))

    def test_no_funding_group_and_ack_has_no_number(self):
        expected = ['ok', '<ack>acknowle<sub />dgements</ack>']

        self.assertEquals(
            expected,
            self._validate('<root><ack>acknowle<sub/>dgements</ack></root>'))

    def test_no_funding_group_and_ack_has_number(self):
        expected = ['e', '<ack>acknowledgements<p>1234</p></ack>']

        self.assertEquals(
            expected,
            self._validate('<root><ack>acknowledgements<p>1234</p></ack></root>'))

    def test_funding_group(self):
        expected = ['ok', '<funding-group>funding data</funding-group>']

        self.assertEquals(expected, self._validate('<root><ack>acknowledgements<funding-group>funding data</funding-group></ack></root>'))


class ISSNCheckingPipeTest(unittest.TestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import ISSNCheckingPipe
        return ISSNCheckingPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root></root>'):
        from StringIO import StringIO
        etree = ElementTree()
        return etree.parse(StringIO(xml_string))

    def _validate(self, xml_string):
        data = self._make_data(xml_string)
        pipe = self._make_pipe(data)
        return pipe.validate(data)

    def test_pipe_issn_with_one_valid_ISSN(self):
        expected = ['ok', '']

        self.assertEquals(
            self._validate("<root><issn pub-type='epub'>0102-6720</issn></root>"), expected)

    def test_pipe_issn_with_one_invalid_ISSN(self):
        expected = ['e', 'neither eletronic ISSN nor print ISSN are valid']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>1234-1234</issn></root>"), expected)

    def test_pipe_issn_with_two_valid_ISSN_eletronic_and_print(self):
        expected = ['ok', '']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>0100-879X</issn><issn pub-type='epub'>1414-431X</issn></root>"), expected)

    def test_pipe_issn_with_strange_ISSN(self):
        expected = ['e', 'neither eletronic ISSN nor print ISSN are valid']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>01ols0-OIN</issn></root>"), expected)

    def test_pipe_issn_with_one_strange_ISSN_and_one_valid_ISSN(self):
        expected = ['ok', '']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>01ols0-OIN</issn><issn pub-type='epub'>1414-431X</issn></root>"), expected)
