# coding: utf-8
import sys

import plumber

import utils
from models import Attempt

class PipeFundingCheck(plumber.Pipe):
    
    def transform(self, data):
        self._warnings = []
        funding_nodes = data.findall('.//funding-group')
        ack_nodes = data.findall('.//ack')
        if len(funding_nodes) == 0:
            # notify absence of funding-group as warning
            # FIXME
            # self.notify('funding-group=0')
            self._warnings.append('funding-group=0')
            
        return data
    
    def warnings(self):
        return '\n'.join(self._warnings)


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
