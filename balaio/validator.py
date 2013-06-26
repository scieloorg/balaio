# coding: utf-8
import sys
import xml.etree.ElementTree as etree

import plumber

import utils
import notifier
from models import Attempt



class ValidationPipe(plumber.Pipe):
    def __init__(self, data, notifier_dep=notifier.Notifier):
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep
        
    def transform(self, data):
        # data = (Attempt, PackageAnalyzer)
        # PackagerAnalyzer.xml
        attempt, package_analyzer = data

        message = {}
        result = self.validate(package_analyzer.xml)

        for k,v in result.items():
            message[k] = v
        
        self._notifier.validation_event(message)

    def validate(self, data):
        return {}

class FundingCheckingPipe(ValidationPipe):
    _stage_ = 'funding-group'

    def validate(self, data):
        status = 'ok'
        description = ''

        funding_nodes = data.findall('.//funding-group')
        
        if len(funding_nodes) == 0:    
            ack_nodes = data.findall('.//ack')
            if len(ack_nodes) > 0:
                ack_text = ''
                for ack_node in ack_nodes:
                    ack_text += etree.tostring(ack_node)

                description = ack_text
                if self._ack_contains_number(ack_text):
                    status = 'e'
                else:
                    status = 'w'
            else:
                status = 'w'
                description = 'no funding-group and no ack was identified'
        else:
            description = etree.tostring(funding_nodes[0])
        result = { 'stage': self._stage_, 'status': status, 'description': description,}
        return result

    
    def _ack_contains_number(self, ack_text):
        number_in_ack = False
        for i in range(0,10):
            if str(i) in ack_text:
                number_in_ack = True
                break
        return number_in_ack

class ExamplePipe(plumber.Pipe):
    def transform(self, data):
        return data


ppl = plumber.Pipeline(ExamplePipe)

if __name__ == '__main__':
    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
