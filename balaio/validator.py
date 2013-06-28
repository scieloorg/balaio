# coding: utf-8
import sys
import xml.etree.ElementTree as etree

import plumber

import utils
import notifier
from models import Attempt

STATUS_OK = 'ok'
STATUS_WARNING = 'w'
STATUS_ERROR = 'e'


class ValidationPipe(plumber.Pipe):
    def __init__(self, data, notifier_dep=notifier.Notifier):
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep

    def transform(self, data):
        # data = (Attempt, PackageAnalyzer)
        # PackagerAnalyzer.xml
        attempt, package_analyzer = data

        result_status, result_description = self.validate(package_analyzer.xml)

        message = {
            'stage': self._stage_,
            'status': result_status,
            'description': result_description,
        }

        self._notifier.validation_event(message)

        return data


class FundingCheckingPipe(ValidationPipe):
    _stage_ = 'funding-group'

    def validate(self, data):
        
        funding_nodes = data.findall('.//funding-group')
        ack_node = data.findall('.//ack') 

        status = STATUS_OK if funding_nodes != [] else STATUS_WARNING
        description = etree.tostring(funding_nodes[0])

        if not status == STATUS_OK:
            description = etree.tostring(ack_node[0]) if ack_node != [] else 'no funding-group and no ack was identified'            
            status = STATUS_ERROR if self._ack_contains_number(description) else STATUS_WARNING
        
        return [ status, description ]
    
    def _ack_contains_number(self, ack_text):
        # if ack_text contains any number

        return any((True for n in xrange(10) if str(n) in ack_text))
        
ppl = plumber.Pipeline(FundingCheckingPipe)

if __name__ == '__main__':
    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
