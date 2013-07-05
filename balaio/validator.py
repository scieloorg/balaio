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

    def compare_registered_data_and_xml_data(self, package_analyzer, mandatory=False):
        """
        Compares the data registered in SciELO Manager and the data in XML ignoring blank spaces and lower/uppercase
        Returns [status, description]
        """
        registered_data = self._registered_data(package_analyzer)
        xml_data = self._xml_data(package_analyzer)

        if registered_data is None and xml_data == '':
            status, description = [STATUS_ERROR, 'Both ' + self._registered_data_label + ' in Manager and ' + self._xml_data_label + ' in XML are mandatory. But both are missing.'] if mandatory is True else [STATUS_OK, xml_data]
        elif registered_data is None:
            status, description = [STATUS_ERROR, self._registered_data_label + ' not found in Manager']
        elif xml_data == '':
            status, description = [STATUS_ERROR, self._xml_data_label + ' not found in XML']
        elif xml_data.lower().replace(' ', '') == registered_data.lower().replace(' ', ''):
            status, description = [STATUS_OK, xml_data]
        else:
            status = STATUS_ERROR
            description = 'Data in XML and Manager do not match.' + '\n' + 'Data in Manager: ' + registered_data + '\n' + 'Data in XML: ' + xml_data
            # + '\n' + xml_data.lower().replace(' ', '-') + '\n' + registered_data.lower().replace(' ', '-')
        return [status, description]


# Pipes to validate journal data
class ISSNValidationPipe(ValidationPipe):
    """
    Verify if the ISSN(s) exist on SciELO scieloapi.Manager and if it`s a valid ISSN.

    Analyzed atribute from ``.//issn``: ``@pub-type="ppub"`` or ``@pub-type="epub"``

    """
    _stage_ = 'issn'

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        journal_eissn = data.findtext(".//issn[@pub-type='epub']")
        journal_pissn = data.findtext(".//issn[@pub-type='ppub']")

        if utils.is_valid_issn(journal_pissn) or utils.is_valid_issn(journal_eissn):
            if journal_pissn:
                #Validate journal_pissn against SciELO scieloapi.Manager
                pass
            if journal_eissn:
                #Validate journal_eissn against SciELO scieloapi.Manager
                pass
            return [STATUS_OK, '']
        else:
            return [STATUS_ERROR, 'neither eletronic ISSN nor print ISSN are valid']


class AbbrevJournalTitleValidationPipe(ValidationPipe):
    """
    Check if journal-meta/abbrev-journal-title[@abbrev-type='publisher'] and the data registered in SciELO Manager matches
    """
    def validate(self, package_analyzer):
        # set registered data label in order to display it in description
        self._registered_data_label = 'title_iso'
        # set xml data label (xpath) in order to display it in description
        self._xml_data_label = './/journal-meta/abbrev-journal-title[@abbrev-type="publisher"]'
        return self.compare_registered_data_and_xml_data(package_analyzer, mandatory=True)

    def _xml_data(self, package_analyzer):
        """
        Returns the content of ``self._xml_data_label`` (xpath in XML)
        """
        node = package_analyzer.xml.find(self._xml_data_label)
        return node.text if not node is None else ''

    def _registered_data(self, package_analyzer):
        """
        Returns the data registered in SciELO Manager
        Gets a single journal by ``package_analyzer.meta[journal_title]``
        then returns the registered data identified by ``self.registered_data_label``
        """
        # gets a single journal by ``package_analyzer.meta[journal_title]``
        journal_data = self._manager.journal(package_analyzer.meta['journal_title'], 'title')
        # returns the registered data identified by ``self._registered_data_label``
        return journal_data.get(self._registered_data_label, None)


class NLMJournalTitleValidationPipe(ValidationPipe):
    """
    Check if journal-meta/journal-id[@journal-id-type='nlm-ta'] and the data registered in SciELO Manager matches
    """
    def validate(self, package_analyzer):
        # set registered data label in order to display it in description
        self._registered_data_label = 'medline_title'
        # set xml data label (xpath) in order to display it in description
        self._xml_data_label = './/journal-meta/journal-id[@journal-id-type="nlm-ta"]'
        return self.compare_registered_data_and_xml_data(package_analyzer)

    def _xml_data(self, package_analyzer):
        """
        Returns the content of ``self._xml_data_label`` (xpath in XML)
        """
        node = package_analyzer.xml.find(self._xml_data_label)
        return node.text if not node is None else ''

    def _registered_data(self, package_analyzer):
        """
        Returns the data registered in SciELO Manager
        Gets a single journal by ``package_analyzer.meta[journal_title]``
        then returns the registered data identified by ``self.registered_data_label``
        """
        # gets a single journal by ``package_analyzer.meta[journal_title]``
        journal_data = self._manager.journal(package_analyzer.meta['journal_title'], 'title')
        # returns the registered data identified by ``self._registered_data_label``
        return journal_data.get(self._registered_data_label, None)


class PublisherNameValidationPipe(ValidationPipe):
    """
    Check if journal-meta/publisher/publisher-name and the data registered in SciELO Manager matches
    """
    def validate(self, package_analyzer):
        # FIXME se varios publisher_name, qual seria o separador? quebra de linha?
        # set registered data label in order to display it in description
        self._registered_data_label = 'publisher_name'
        # set xml data label (xpath) in order to display it in description
        self._xml_data_label = './/journal-meta/publisher/publisher-name'
        return self.compare_registered_data_and_xml_data(package_analyzer, mandatory=True)

    def _xml_data(self, package_analyzer):
        """
        Returns the content of ``self._xml_data_label`` (xpath in XML)
        """
        node = package_analyzer.xml.find(self._xml_data_label)
        return node.text if not node is None else ''

    def _registered_data(self, package_analyzer):
        """
        Returns the data registered in SciELO Manager
        Gets a single journal by ``package_analyzer.meta[journal_title]``
        then returns the registered data identified by ``self.registered_data_label``
        """
        # gets a single journal by ``package_analyzer.meta[journal_title]``
        journal_data = self._manager.journal(package_analyzer.meta['journal_title'], 'title')
        # returns the registered data identified by ``self._registered_data_label``
        return journal_data.get(self._registered_data_label, None)

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
