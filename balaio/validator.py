# coding: utf-8
import sys

import plumber

import utils
import notifier
from models import Attempt



class ValidationPipe(plumber.Pipe):
    def __init__(self, data, notifier_dep=notifier.Notifier):
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep
        
    def transform(self, data):
        result = self.validate(data)

        for k,v in self._result.items():
            message[k] = v
        
        self._notifier.validation_event(message)

    def validate(self, data):


class FundingCheckingPipe(ValidationPipe):
    _stage_ = 'funding-group'

    def validate(self, data):
        funding_nodes = data.findall('.//funding-group')
        
        if len(funding_nodes) == 0:    
            ack_nodes = data.findall('.//ack')
            if len(ack_nodes) > 0:
                ack_text = self._node_text(ack_nodes)
        
                if self._ack_contains_number(ack_text):
                    status = 'e'
                    description = '<ack>' + ack_text + '</ack>'
                else:
                    status = 'w'
                    description = '<ack>' + ack_text + '</ack>'
            else:
                status = 'w'
                description = 'no funding-group and no ack was identified'
        else:
            status = 'ok'
            description = ''

        result = {
            'stage': _stage_, 
            'status': status, 
            'description': description,
        }
        return result

    def _node_text(self, nodes):
        text = ''
        for node in nodes:
             text += node.text
        
        return text

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
