# coding: utf-8
import sys
import utils
import plumber
import notifier
import scieloapi
import xml.etree.ElementTree as etree

from utils import Configuration

config = Configuration.from_env()

STATUS_OK = 'ok'
STATUS_WARNING = 'w'
STATUS_ERROR = 'e'


class ValidationPipe(plumber.Pipe):
    """
    Specialized Pipe which validates the data and notifies the result
    """
    def __init__(self, data, manager_dep=scieloapi.Manager, notifier_dep=notifier.Notifier):
        super(ValidationPipe, self).__init__(data)
        self._notifier = notifier_dep()
        self._manager = manager_dep()

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

    def compare_registered_data_and_xml_data(self, package_analyzer):
        """
        Compare registered data in scieloapi.Manager to data in XML
        Returns [status, description]
        """
        registered_data = self._registered_data(package_analyzer)
        xml_data = self._xml_data(package_analyzer)

        if registered_data is None and xml_data == '':
            status, description = [STATUS_OK, xml_data]
        elif registered_data is None:
            status, description = [STATUS_ERROR, self._registered_data_label + ' not found in Manager']
        elif xml_data == '':
            status, description = [STATUS_ERROR, self._xml_data_label + ' not found in XML']
        elif xml_data == registered_data:
            status, description = [STATUS_OK, xml_data]
        else:
            status = STATUS_ERROR
            description = 'Data in XML and Manager do not match.' + '\n' + 'Data in Manager: ' + registered_data + '\n' + 'Data in XML: ' + xml_data
        return [status, description]


# Pipes to validate journal data
class ISSNValidationPipe(ValidationPipe):
    """
    Verify if the ISSN(s) exist on SciELO scieloapi.Manager and if it`s a valid ISSN.

    Analyzed atribute from ``.//issn``: ``@pub-type="ppub"`` or ``@pub-type="epub"``

    """
    _stage_ = 'issn'

    def _xml_data(self, package_analyzer):
        node = package_analyzer.xml.findtext(".//issn[@pub-type='epub']")
        return node if node else ''

    def _registered_data(self, package_analyzer):
        return self._manager.journal(package_analyzer.meta['journal_title'], 'title').get(self._registered_data_label, None)

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        journal_eissn = data.findtext(".//issn[@pub-type='epub']")
        journal_pissn = data.findtext(".//issn[@pub-type='ppub']")

        if utils.is_valid_issn(journal_pissn) or utils.is_valid_issn(journal_eissn):

            if journal_pissn:
                self._registered_data_label = 'print_issn'
                self._xml_data_label = journal_pissn
                return self.compare_registered_data_and_xml_data(package_analyzer)

            if journal_eissn:
                self._registered_data_label = 'eletronic_issn'
                self._xml_data_label = journal_eissn
                return self.compare_registered_data_and_xml_data(package_analyzer)
        else:
            return [STATUS_ERROR, 'neither eletronic ISSN nor print ISSN are valid']


class AbbrevJournalTitleValidationPipe(ValidationPipe):
    """
    Check if journal-meta/abbrev-journal-title[@abbrev-type='publisher'] is the same as registered in scieloapi.Manager
    """

    def _xml_data(self, package_analyzer):
        node = package_analyzer.xml.findtext(self._xml_data_label)
        return node if node else ''

    def _registered_data(self, package_analyzer):
        return self._manager.journal(package_analyzer.meta['journal_title'], 'title').get(self._registered_data_label, None)

    def validate(self, package_analyzer):
        self._registered_data_label = 'title_iso'
        self._xml_data_label = './/journal-meta/abbrev-journal-title[@abbrev-type="publisher"]'
        return self.compare_registered_data_and_xml_data(package_analyzer)


class NLMJournalTitleValidationPipe(ValidationPipe):
    """
    Check if journal-meta/journal-id[@journal-id-type='nlm-ta'] is the same as registered in Manager
    """
    def validate(self, package_analyzer):
        self._registered_data_label = 'medline_title'
        self._xml_data_label = './/journal-meta/journal-id[@journal-id-type="nlm-ta"]'
        return self.compare_registered_data_and_xml_data(package_analyzer)

    def _xml_data(self, package_analyzer):
        node = package_analyzer.xml.findtext(self._xml_data_label)
        return node if node else ''

    def _registered_data(self, package_analyzer):
        return self._manager.journal(package_analyzer.meta['journal_title'], 'title').get(self._registered_data_label, None)

# Pipes to validate issue data


# Pipes to validate article data
class FundingValidationPipe(ValidationPipe):
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


ppl = plumber.Pipeline(ISSNValidationPipe, AbbrevJournalTitleValidationPipe, NLMJournalTitleValidationPipe, FundingValidationPipe)

if __name__ == '__main__':
    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
