import mocker
from xml.etree.ElementTree import ElementTree
import json
from StringIO import StringIO

from balaio import validator
from balaio import notifier

class FundingCheckingPipeTest(mocker.MockerTestCase):

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
