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
    """
    Specialized Pipe which validates the data and notifies the result
    """
    def __init__(self, data, notifier_dep=notifier.Notifier):
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep

    def transform(self, data):
        # data = (Attempt, PackageAnalyzer)
        # PackagerAnalyzer.xml
        attempt, package_analyzer = data

        result_status, result_description = self.validate(package_analyzer)

        message = {
            'stage': self._stage_,
            'status': result_status,
            'description': result_description,
        }

        self._notifier.validation_event(message)

        return data


class FundingCheckingPipe(ValidationPipe):
    """
    Check the absence/presence of funding-group and ack in the document

    funding-group is a mandatory element only if there is contract or project number
    in the document. Sometimes this information comes in Acknowledgments section.
    Return
    [STATUS_ERROR, ack]           if no founding-group, but Acknowledgments (ack) has number
    [STATUS_OK, founding-group]   if founding-group is present
    [STATUS_OK, ack]              if no founding-group, but Acknowledgments has no numbers
    [STATUS_WARNING, 'no funding-group and no ack'] if founding-group and Acknowledgments (ack) are absents
    """
    _stage_ = 'funding-group'

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        funding_nodes = data.findall('.//funding-group')

        status, description = [STATUS_OK, etree.tostring(funding_nodes[0])] if funding_nodes != [] else [STATUS_WARNING, 'no funding-group']   
        if not status == STATUS_OK:
            ack_node = data.findall('.//ack')
            description = etree.tostring(ack_node[0]) if ack_node != [] else 'no funding-group and no ack'
            status = STATUS_ERROR if self._contains_number(description) else STATUS_OK if description != 'no funding-group and no ack' else STATUS_WARNING
        return [status, description]

    def _contains_number(self, text):
        # if text contains any number
        return any((True for n in xrange(10) if str(n) in text))


ppl = plumber.Pipeline(FundingCheckingPipe)

if __name__ == '__main__':
    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
