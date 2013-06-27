import unittest
from xml.etree.ElementTree import ElementTree

from balaio import validator

class FundingCheckingPipeTest(unittest.TestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import FundingCheckingPipe
        return FundingCheckingPipe(*args, **kwargs)

    def _make_data(self, xml_string = '<root></root>'):
        from StringIO import StringIO
        etree = ElementTree()
        return etree.parse(StringIO(xml_string))

    def _validate(self, xml_string):
        data = self._make_data(xml_string)
        pipe = self._make_pipe(data)
        return pipe.validate(data)

    def test_no_funding_group_and_no_ack(self):
        expected = ['w', 'no funding-group and no ack was identified']

        self.assertEquals(
            expected, 
            self._validate('<root></root>'))
        
    def test_no_funding_group_and_ack_has_no_number(self):
        expected = ['w', '<ack>acknowle<sub />dgements</ack>']

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