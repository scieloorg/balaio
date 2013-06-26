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
        expected = {
            'stage':'funding-group',
            'status':'w',
            'description':'no funding-group and no ack was identified',            
            }
        
        result = self._validate('<root></root>')
        
        self.assertEquals(expected['stage'], result['stage'])
        self.assertEquals(expected['status'], result['status'])
        self.assertEquals(expected['description'], result['description'])

    def test_no_funding_group_and_ack_has_no_number(self):
        expected = {
            'stage':'funding-group',
            'status':'w',
            'description':'<ack>acknowle<sub />dgements</ack>',            
            }
        
        result = self._validate('<root><ack>acknowle<sub/>dgements</ack></root>')
        
        self.assertEquals(expected['stage'], result['stage'])
        self.assertEquals(expected['status'], result['status'])
        self.assertEquals(expected['description'], result['description'])

    def test_no_funding_group_and_ack_has_number(self):
        expected = {
            'stage':'funding-group',
            'status':'e',
            'description':'<ack>acknowledgements<p>1234</p></ack>',            
            }
        result = self._validate('<root><ack>acknowledgements<p>1234</p></ack></root>')
        
        self.assertEquals(expected['stage'], result['stage'])
        self.assertEquals(expected['status'], result['status'])
        self.assertEquals(expected['description'], result['description'])

    def test_funding_group(self):
        expected = {
            'stage':'funding-group',
            'status':'ok',
            'description':'<funding-group>funding data</funding-group>',            
            }
        result = self._validate('<root><ack>acknowledgements<funding-group>funding data</funding-group></ack></root>')
        
        self.assertEquals(expected['stage'], result['stage'])
        self.assertEquals(expected['status'], result['status'])
        self.assertEquals(expected['description'], result['description'])
