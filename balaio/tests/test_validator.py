#coding: utf-8
import json
import mocker
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree


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
        expected = ['e', 'Data in XML and Manager do not match.\nData in Manager: Rev. Bras. ????\nData in XML: Rev Bras ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><abbrev-journal-title abbrev-type="publisher">Rev Bras ????</abbrev-journal-title></journal-meta></root>'))


class ISSNCheckingPipeTest(mocker.MockerTestCase):

    def _make_pipe(self, *args, **kwargs):
        from balaio.validator import ISSNValidationPipe
        return ISSNValidationPipe(*args, **kwargs)

    def _make_etree(self, xml):
        etree = ElementTree()
        return etree.parse(StringIO(xml))

    def _make_xml(self, issn_type, issn):
        return """
               <root>
                   <journal-title>Acta Paulista de Enfermagem</journal-title>
                   <issn pub-type='%s'>%s</issn>
               </root>
               """ % (issn_type, issn)

    def _make_json(self, dict_data):
        return json.load(StringIO(dict_data))

    def test_pipe_issn_with_one_valid_ISSN(self):

        xml = self._make_etree(self._make_xml('epub', '0102-6720'))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        self.mocker.count(2)

        pkg_analyzer.meta
        self.mocker.result({"journal_title": "Acta Paulista de Enfermagem", "journal_eissn": "0102-6720"})

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        mock_manager.journal("Acta Paulista de Enfermagem", "title")
        self.mocker.result(self._make_json('{"title": "Acta Paulista de Enfermagem", "eletronic_issn": "0102-6720"}'))

        self.mocker.replay()

        pipe = self._make_pipe((attempt, pkg_analyzer), mock_manager, mock_notifier)

        self.assertEquals(pipe.validate(pkg_analyzer), ['ok', '0102-6720'])

    def test_pipe_issn_with_one_invalid_ISSN(self):

        xml = self._make_etree(self._make_xml('epub', '1234-1234'))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        self.mocker.replay()

        pipe = self._make_pipe((attempt, pkg_analyzer), mock_manager, mock_notifier)

        self.assertEquals(pipe.validate(pkg_analyzer), ['e', 'neither eletronic ISSN nor print ISSN are valid'])

    def test_pipe_issn_with_strange_ISSN(self):

        xml = self._make_etree(self._make_xml('epub', '01ols0-OIN'))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        self.mocker.replay()

        pipe = self._make_pipe((attempt, pkg_analyzer), mock_manager, mock_notifier)

        self.assertEquals(pipe.validate(pkg_analyzer), ['e', 'neither eletronic ISSN nor print ISSN are valid'])

    def test_pipe_issn_with_unregistred_ISSN(self):
        xml = self._make_etree(self._make_xml('epub', '0102-6720'))

        attempt = self.mocker.mock()
        pkg_analyzer = self.mocker.mock()
        mock_manager = self.mocker.mock()
        mock_notifier = self.mocker.mock()

        pkg_analyzer.xml
        self.mocker.result(xml)

        self.mocker.count(2)

        pkg_analyzer.meta
        self.mocker.result({"journal_title": "Acta Paulista de Enfermagem", "journal_eissn": "0102-6720"})

        mock_notifier()
        self.mocker.result(mock_notifier)

        mock_manager()
        self.mocker.result(mock_manager)

        mock_manager.journal("Acta Paulista de Enfermagem", "title")
        self.mocker.result(self._make_json('{"title": "Acta Paulista de Enfermagem", "eletronic_issn": "0102-6820"}'))

        self.mocker.replay()

        pipe = self._make_pipe((attempt, pkg_analyzer), mock_manager, mock_notifier)

        self.assertEquals(pipe.validate(pkg_analyzer), ['e', u'Data in XML and Manager do not match.\nData in Manager: 0102-6820\nData in XML: 0102-6720'])


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
        expected = ['e', 'Data in XML and Manager do not match.\nData in Manager: Rev. Bras. ????\nData in XML: Rev Bras ????']

        self.assertEquals(
            expected,
            self._validate('<root><journal-meta><journal-id journal-id-type="nlm-ta">Rev Bras ????</journal-id></journal-meta></root>'))
