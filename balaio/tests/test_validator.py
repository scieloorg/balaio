import json
import mocker
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree

from balaio import validator
from balaio import notifier


class FundingValidationPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import FundingValidationPipe
        return FundingValidationPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root><journal-title>Revista Brasileira ...</journal-title></root>'):

        etree = ElementTree()
        xml = etree.parse(StringIO(xml_string))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        return (attempt, pkg_analyzer)

    def _validate(self, xml_string):
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        data = self._make_data(xml_string)
        self.mocker.replay()

        pipe = self._make_pipe(data, mock_manager, mock_notifier)
        return pipe.validate(data[1])

    def test_no_funding_group_and_no_ack(self):
        expected = ['w', 'no funding-group and no ack']

        self.assertEquals(
            expected,
            self._validate('<root></root>'))

    def test_no_funding_group_and_ack_has_no_number(self):
        expected = ['ok', '<ack>acknowle<sub />dgements</ack>']

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


class AbbrevJournalTitleValidationPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import AbbrevJournalTitleValidationPipe
        return AbbrevJournalTitleValidationPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root><journal-title>Revista Brasileira ...</journal-title></root>'):

        etree = ElementTree()
        xml = etree.parse(StringIO(xml_string))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        pkg_analyzer.meta
        self.mocker.result({'journal_title': 'Revista Brasileira ...'})

        return (attempt, pkg_analyzer)

    def _validate(self, xml_string, manager_result='{"journal-title":"Revista Brasileira ...", "title_iso": "Rev. Bras. ????"}'):
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        mock_manager.journal('Revista Brasileira ...', 'title')
        self.mocker.result(json.load(StringIO(manager_result)))

        data = self._make_data(xml_string)
        self.mocker.replay()

        pipe = self._make_pipe(data, mock_manager, mock_notifier)
        return pipe.validate(data[1])

    def test_abbrev_journal_title_is_valid(self):
        expected = ['ok', 'Rev. Bras. ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><abbrev-journal-title abbrev-type="publisher">Rev. Bras. ????</abbrev-journal-title></journal-meta></root>'))

    def test_abbrev_journal_title_not_found_in_xml(self):
        expected = ['e', './/journal-meta/abbrev-journal-title[@abbrev-type="publisher"] not found in XML']
        self.assertEquals(
            expected,
            self._validate('<root><abbrev-journal-title>titulo abreviado</abbrev-journal-title></root>'))

    def test_abbrev_journal_title_not_found_in_manager(self):
        expected = ['e', 'title_iso not found in Manager']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><abbrev-journal-title abbrev-type="publisher">Rev. Bras. ????</abbrev-journal-title></journal-meta></root>', '{"journal-title":"Revista Brasileira ..."}'))

    def test_abbrev_journal_title_not_matched(self):
        expected = ['e', u'Data in XML and Manager do not match.' + '\n' + 'Data in Manager: Rev. Bras. ????' + '\n' + 'Data in XML: Rev Bras ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><abbrev-journal-title abbrev-type="publisher">Rev Bras ????</abbrev-journal-title></journal-meta></root>'))


class ISSNCheckingPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import ISSNValidationPipe
        return ISSNValidationPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root></root>'):
        etree = ElementTree()
        xml = etree.parse(StringIO(xml_string))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        return (attempt, pkg_analyzer)

    def _validate(self, xml_string):
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        data = self._make_data(xml_string)
        self.mocker.replay()

        pipe = self._make_pipe(data, mock_manager, mock_notifier)
        return pipe.validate(data[1])

    def test_pipe_issn_with_one_valid_ISSN(self):
        expected = ['ok', '']

        self.assertEquals(
            self._validate("<root><issn pub-type='epub'>0102-6720</issn></root>"), expected)

    def test_pipe_issn_with_one_invalid_ISSN(self):
        expected = ['e', 'neither eletronic ISSN nor print ISSN are valid']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>1234-1234</issn></root>"), expected)

    def test_pipe_issn_with_two_valid_ISSN_eletronic_and_print(self):
        expected = ['ok', '']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>0100-879X</issn><issn pub-type='epub'>1414-431X</issn></root>"), expected)

    def test_pipe_issn_with_strange_ISSN(self):
        expected = ['e', 'neither eletronic ISSN nor print ISSN are valid']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>01ols0-OIN</issn></root>"), expected)

    def test_pipe_issn_with_one_strange_ISSN_and_one_valid_ISSN(self):
        expected = ['ok', '']

        self.assertEquals(
            self._validate("<root><issn pub-type='ppub'>01ols0-OIN</issn><issn pub-type='epub'>1414-431X</issn></root>"), expected)


class NLMJournalTitleValidationPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import NLMJournalTitleValidationPipe
        return NLMJournalTitleValidationPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root><journal-title>Revista Brasileira ...</journal-title></root>'):

        etree = ElementTree()
        xml = etree.parse(StringIO(xml_string))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        pkg_analyzer.meta
        self.mocker.result({'journal_title': 'Revista Brasileira ...'})

        return (attempt, pkg_analyzer)

    def _validate(self, xml_string, manager_result='{"journal-title":"Revista Brasileira ...", "medline_title": "Rev. Bras. ????"}'):
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        mock_manager.journal('Revista Brasileira ...', 'title')
        self.mocker.result(json.load(StringIO(manager_result)))

        data = self._make_data(xml_string)
        self.mocker.replay()

        pipe = self._make_pipe(data, mock_manager, mock_notifier)
        return pipe.validate(data[1])

    def test_nlm_journal_title_is_valid(self):
        expected = ['ok', 'Rev. Bras. ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><journal-id journal-id-type="nlm-ta">Rev. Bras. ????</journal-id></journal-meta></root>'))

    def test_nlm_journal_not_found_in_xml_and_not_found_in_manager(self):
        expected = ['ok', '']
        self.assertEquals(
            expected,
            self._validate('<root><abbrev-journal-title>titulo abreviado</abbrev-journal-title></root>', '{"journal-title":"Revista Brasileira ..."}'))

    def test_nlm_journal_title_not_found_in_xml(self):
        expected = ['e', './/journal-meta/journal-id[@journal-id-type="nlm-ta"] not found in XML']
        self.assertEquals(
            expected,
            self._validate('<root><abbrev-journal-title>titulo abreviado</abbrev-journal-title></root>'))

    def test_nlm_journal_title_not_found_in_manager(self):
        expected = ['e', 'medline_title not found in Manager']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><journal-id journal-id-type="nlm-ta">Rev. Bras. ????</journal-id></journal-meta></root>', '{"journal-title":"Revista Brasileira ..."}'))

    def test_nlm_journal_title_not_matched(self):
        expected = ['e', u'Data in XML and Manager do not match.' + '\n' + 'Data in Manager: Rev. Bras. ????' + '\n' + 'Data in XML: Rev Bras ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><journal-id journal-id-type="nlm-ta">Rev Bras ????</journal-id></journal-meta></root>'))


class PublisherNameValidationPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import PublisherNameValidationPipe
        return PublisherNameValidationPipe(*args, **kwargs)

    def _make_data(self, xml_string='<root><journal-title>Revista Brasileira ...</journal-title></root>'):

        etree = ElementTree()
        xml = etree.parse(StringIO(xml_string))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        pkg_analyzer.meta
        self.mocker.result({'journal_title': 'Revista Brasileira ...'})

        return (attempt, pkg_analyzer)

    def _validate(self, xml_string, manager_result='{"journal-title":"Revista Brasileira ...", "publisher_name": "Publicador ????"}'):
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        mock_manager.journal('Revista Brasileira ...', 'title')
        self.mocker.result(json.load(StringIO(manager_result)))

        data = self._make_data(xml_string)
        self.mocker.replay()

        pipe = self._make_pipe(data, mock_manager, mock_notifier)
        return pipe.validate(data[1])

    def test_publisher_name_is_valid(self):
        expected = ['ok', 'Publicador   ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><publisher><publisher-name>Publicador   ????</publisher-name></publisher></journal-meta></root>'))

    def test_publisher_name_not_found_in_xml_and_not_found_in_manager(self):
        expected = ['e', 'Both publisher_name in Manager and .//journal-meta/publisher/publisher-name in XML are mandatory. But both are missing.']
        self.assertEquals(
            expected,
            self._validate('<root><abbrev-journal-title>titulo abreviado</abbrev-journal-title></root>', '{"journal-title":"Revista Brasileira ..."}'))

    def test_publisher_name_not_found_in_xml(self):
        expected = ['e', './/journal-meta/publisher/publisher-name not found in XML']
        self.assertEquals(
            expected,
            self._validate('<root><abbrev-journal-title>titulo abreviado</abbrev-journal-title></root>'))

    def test_publisher_name_not_found_in_manager(self):
        expected = ['e', 'publisher_name not found in Manager']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><publisher><publisher-name>Publicador   ????</publisher-name></publisher></journal-meta></root>', '{"journal-title":"Revista Brasileira ..."}'))

    def test_publisher_name_not_matched(self):
        expected = ['e', u'Data in XML and Manager do not match.' + '\n' + 'Data in Manager: Publicador ????' + '\n' + 'Data in XML: Publ~icador   ??***??']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><publisher><publisher-name>Publ~icador   ??***??</publisher-name></publisher></journal-meta></root>'))
