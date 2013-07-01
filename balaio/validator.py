# coding: utf-8
import sys
import xml.etree.ElementTree as etree
import json

import plumber

import utils
import notifier
from models import Attempt

STATUS_OK = 'ok'
STATUS_WARNING = 'w'
STATUS_ERROR = 'e'


def compare_registered_data_and_xml_data(self, registered_data, xml_data):
    """
    Compare registered data in Manager to data in XML
    Returns [status, description]
    """
    status, description = [STATUS_OK, '']
    if xml_data != registered_data:
        status = STATUS_ERROR
        description = 'Data in XML and Manager do not match.\nData in Manager: ' + registered_data + '\nData in XML: ' + xml_data
    return [status, description]


def etree_nodes_value(self, etree, xpath):
    """
    Returns content of a given ``xpath`` of ``etree``
    """
    return '\n'.join([node.text for node in etree.findall(xpath)])


class Manager(object):
    """
    Manager
    """
    def __init__(self):
        super(Manager, self).__init__()

    def do_query(self, query):
        #FIXME execute SciELO Manager API instead
        return '{"journal": {"journal-title":"Revista Brasileira ..."}'


class ManagerData(object):
    """
    ManagerData
    """
    def __init__(self, json_data):
        super(ManagerData, self).__init__()
        self._data = json.load(json_data)

    def abbrev_journal_title(self):
        # FIXME
        return self._data['abbrev-journal-title'] if 'abbrev-journal-title' in self._data.keys() else ''


class ValidationPipe(plumber.Pipe):
    """
    Specialized Pipe which validates the data and notifies the result
    """
    def __init__(self, data, manager_dep=Manager, notifier_dep=notifier.Notifier):
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep()
        self._manager_data = ManagerData(manager_dep().do_query(data.xml.journal_title))

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


# Pipes to validate journal data
class AbbrevJournalTitleValidationPipe(ValidationPipe):
    """
    Check if journal-meta/abbrev-journal-title[@abbrev-type='publisher'] is the same as registered in Manager
    """

    def validate(self, package_analyzer):
        xml_data = etree_nodes_value(package_analyzer.xml, './/journal-meta/abbrev-journal-title[@abbrev-type="publisher"]')
        registered_data = self._manager_data.abbrev_journal_title()
        return compare_registered_data_and_xml_data(registered_data, xml_data)


# Pipes to validate issue data


# Pipes to validate article data
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
