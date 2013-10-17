# coding: utf-8
import re
import sys
import logging
import xml.etree.ElementTree as etree
import calendar

import scieloapi

import vpipes
import utils
import checkin
import notifier
import scieloapitoolbelt
import models


logger = logging.getLogger('balaio.validator')


class SetupPipe(vpipes.Pipe):

    def __init__(self, notifier, scieloapi, sapi_tools, pkg_analyzer, issn_validator):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._pkg_analyzer = pkg_analyzer
        self._issn_validator = issn_validator

    def _fetch_journal_data(self, criteria):
        """
        Encapsulates the two-phase process of retrieving
        data from one journal matching the criteria.

        :param criteria: valid criteria to retrieve journal data
        :returns: data of one journal
        """
        #cli.fetch_relations(cli.get(i['resource_uri']))
        found_journal = self._scieloapi.journals.filter(
            limit=1, **criteria)
        return self._sapi_tools.get_one(found_journal)

    def _fetch_journal_and_issue_data(self, **criteria):
        """
        Encapsulates the two-phase process of retrieving
        data from one issue matching the criteria.

        :param criteria: valid criteria to retrieve issue data
        :returns: data of one issue
        """
        #cli.fetch_relations(cli.get(i['resource_uri']))
        found_journal_issues = self._scieloapi.issues.filter(
            limit=1, **criteria)
        return self._scieloapi.fetch_relations(self._sapi_tools.get_one(found_journal_issues))

    @vpipes.precondition(vpipes.attempt_is_valid)
    def transform(self, attempt):
        """
        Adds some data that will be needed during validation
        workflow.

        :param attempt: is an models.Attempt instance.
        :returns: a tuple (Attempt, PackageAnalyzer, journal_and_issue_data)
        """
        logger.debug('%s started processing %s' % (self.__class__.__name__, attempt))

        self._notifier(attempt).start()

        pkg_analyzer = self._pkg_analyzer(attempt.filepath)
        pkg_analyzer.lock_package()

        criteria = {}

        if attempt.articlepkg.issue_volume:
            criteria['volume'] = attempt.articlepkg.issue_volume
        if attempt.articlepkg.issue_number:
            criteria['number'] = attempt.articlepkg.issue_number
        if attempt.articlepkg.issue_suppl_volume:
            criteria['suppl_volume'] = attempt.articlepkg.issue_suppl_volume
        if attempt.articlepkg.issue_suppl_number:
            criteria['suppl_number'] = attempt.articlepkg.issue_suppl_number

        journal_pissn = attempt.articlepkg.journal_pissn

        if journal_pissn and self._issn_validator(journal_pissn):
            try:
                journal_and_issue_data = self._fetch_journal_and_issue_data(
                    print_issn=journal_pissn, **criteria)
            except ValueError:
                # unknown pissn
                journal_and_issue_data = None

        journal_eissn = attempt.articlepkg.journal_eissn
        if journal_eissn and self._issn_validator(journal_eissn) and not journal_and_issue_data:
            try:
                journal_and_issue_data = self._fetch_journal_and_issue_data(
                    eletronic_issn=journal_eissn, **criteria)
            except ValueError:
                # unknown eissn
                journal_and_issue_data = None

        if not journal_and_issue_data:
            logger.info('%s is not related to a known journal' % attempt)
            attempt.is_valid = False

        return_value = (attempt, pkg_analyzer, journal_and_issue_data)
        logger.debug('%s returning %s' % (self.__class__.__name__, ','.join([repr(val) for val in return_value])))
        return return_value


class TearDownPipe(vpipes.Pipe):
    def __init__(self, notifier, scieloapi, sapi_tools, pkg_analyzer):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._pkg_analyzer = pkg_analyzer

    def transform(self, item):
        """
        :param item:
        """
        try:
            attempt, pkg_analyzer, __ = item
        except TypeError:
            attempt = item

        logger.debug('%s started processing %s' % (self.__class__.__name__, item))

        try:
            self._notifier(attempt).end()
        except RuntimeError:
            pass

        if 'pkg_analyzer' in locals():
            pkg_analyzer.restore_perms()

        if not attempt.is_valid:
            utils.mark_as_failed(attempt.filepath)

        logger.info('Finished validating %s' % attempt)


class PublisherNameValidationPipe(vpipes.ValidationPipe):
    """
    Validate the publisher name in article `.//journal-meta/publisher/publisher-name`,
    comparing it to the registered publisher name in journal data.
    """
    _stage_ = 'Journal'

    def __init__(self, notifier, scieloapi, sapi_tools, pkg_analyzer, normalize_data):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._pkg_analyzer = pkg_analyzer
        self._normalize_data = normalize_data

    def validate(self, item):
        """
        Performs a validation to one `item` of data iterator.

        :param item: a tuple (models.Attempt, checkin.PackageAnalyzer, a dict of journal issue data).
        :returns: result of the validation in this format [status, description]
        """
        attempt, pkg_analyzer, journal_and_issue_data = item
        j_publisher_name = journal_and_issue_data.get('journal', {}).get('publisher_name', None)
        if j_publisher_name:
            data = pkg_analyzer.xml
            xml_publisher_name = data.findtext('.//journal-meta/publisher/publisher-name')

            if xml_publisher_name:
                if self._normalize_data(xml_publisher_name) == self._normalize_data(j_publisher_name):
                    r = [models.Status.ok, '']
                else:
                    r = [models.Status.error, j_publisher_name + ' [journal]\n' + xml_publisher_name + ' [article]']
            else:
                r = [models.Status.error, 'Missing publisher-name in article']
        else:
            r = [models.Status.error, 'Missing publisher_name in journal']
        return r


class ReferenceValidationPipe(vpipes.ValidationPipe):
    """
    Validate if exist the tag ref-list.
    Analyzed tag: ``.//ref-list/ref``
    """
    _stage_ = 'References'

    def __init__(self, notifier, pkg_analyzer):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer

    def validate(self, item):
        """
        The article may be a editorial why return a warning if no references
        """
        attempt, pkg_analyzer, journal_and_issue_data = item
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            return [models.Status.ok, '']
        else:
            return [models.Status.warning, 'tag reference missing']


class ReferenceSourceValidationPipe(vpipes.ValidationPipe):
    """
    Validate the tag source references
    Verify if exists tag source references
    Verify if exists content in tag source
    Analized tag: ``.//ref-list/ref/element-citation/source``
    """
    _stage_ = 'References'

    def __init__(self, notifier, pkg_analyzer):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer

    def validate(self, item):

        lst_errors = []
        attempt, pkg_analyzer, journal_and_issue_data = item
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            for ref in refs:
                source = ref.find(".//source")

                if source is not None:
                    if source.text is None:
                        lst_errors.append((ref.attrib['id'], 'missing content in tag source'))
                else:
                    lst_errors.append((ref.attrib['id'], 'missing tag source'))

        if lst_errors:
            msg_error = ''

            for ref_id, msg in lst_errors:
                msg_error += ' %s: %s' % (ref_id, msg)

        return [models.Status.error, msg_error] if lst_errors else [models.Status.ok, '']


class ReferenceYearValidationPipe(vpipes.ValidationPipe):
    """
    Validate the tag year references
    Verify if exists tag year references
    Verify if exists content in tag year
    Verify the format of the year, example: ``1999``
    Analized tag: ``.//ref-list/ref/element-citation/year``
    """
    _stage_ = 'References'

    def __init__(self, notifier, pkg_analyzer):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer

    def validate(self, item):

        lst_errors = []

        attempt, pkg_analyzer, journal_and_issue_data = item
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            for ref in refs:
                year = ref.find(".//year")

                if year is not None:
                    if year.text is None:
                        lst_errors.append((ref.attrib['id'], 'missing content in tag year'))
                    else:
                        if not re.search(r'\d{4}', year.text):
                            lst_errors.append((ref.attrib['id'], 'date format is not good'))
                else:
                    lst_errors.append((ref.attrib['id'], 'missing tag year'))

        if lst_errors:
            msg_error = ''

            for ref_id, msg in lst_errors:
                msg_error += ' %s: %s' % (ref_id, msg)

        return [models.Status.error, msg_error] if lst_errors else [models.Status.ok, '']


class ReferenceJournalTypeArticleTitleValidationPipe(vpipes.ValidationPipe):
    """
    Validate the tag article-title references when type is Journal.
    Analized tag: ``.//ref-list/ref/element-citation[@publication-type='journal']/article-title``
    """
    _stage_ = 'References'

    def __init__(self, notifier, pkg_analyzer):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer

    def validate(self, item):

        lst_errors = []

        attempt, pkg_analyzer, journal_and_issue_data = item
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            for ref in refs:
                article_title = ref.find(".//element-citation[@publication-type='journal']/article-title")

                if article_title is not None:
                    if article_title.text is None:
                        lst_errors.append((ref.attrib['id'], 'missing content in tag article-title'))
                else:
                    lst_errors.append((ref.attrib['id'], 'missing tag article-title'))

        if lst_errors:
            msg_error = ''

            for ref_id, msg in lst_errors:
                msg_error += ' %s: %s' % (ref_id, msg)

        return [models.Status.error, msg_error] if lst_errors else [models.Status.ok, '']


class JournalAbbreviatedTitleValidationPipe(vpipes.ValidationPipe):
    """
    Checks exist abbreviated title on source and xml
    Verify if abbreviated title of the xml is equal to source
    """
    _stage_ = 'Journal'

    def __init__(self, notifier, pkg_analyzer, scieloapi, normalize_data):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer
        self._scieloapi = scieloapi
        self._normalize_data = normalize_data

    def validate(self, item):

        attempt, pkg_analyzer, journal_and_issue_data = item
        abbrev_title = journal_and_issue_data.get('journal').get('short_title')

        if abbrev_title:
            abbrev_title_xml = pkg_analyzer.xml.find('.//journal-meta/abbrev-journal-title[@abbrev-type="publisher"]')
            if abbrev_title_xml is not None:
                if self._normalize_data(abbrev_title) == self._normalize_data(abbrev_title_xml.text):
                    return [models.Status.ok, '']
                else:
                    return [models.Status.error, 'the abbreviated title in xml is defferent from the abbreviated title in the source']
            else:
                return [models.Status.error, 'missing abbreviated title in xml']
        else:
            return [models.Status.error, 'missing abbreviated title in source']


class FundingGroupValidationPipe(vpipes.ValidationPipe):
    """
    Validate Funding Group according to the following rules:
    Funding group is mandatory only if there is contract number in the article,
    and this data is usually in acknowledge
    """
    _stage_ = 'Article'

    def __init__(self, notifier, pkg_analyzer):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer

    def validate(self, item):
        """
        Validate funding-group according to the following rules

        :param item: a tuple of (Attempt, PackageAnalyzer, journal_data)
        :returns: [models.Status.warning, ack content], if no founding-group, but Acknowledgments (ack) has number
        :returns: [models.Status.ok, founding-group content], if founding-group is present
        :returns: [models.Status.ok, ack content], if no founding-group, but Acknowledgments has no numbers
        :returns: [models.Status.warning, 'no funding-group and no ack'], if founding-group and Acknowledgments (ack) are absents
        """
        def _contains_number(text):
            """
            Check if it has any number

            :param text: string
            :returns: True if there is any number in text
            """
            return any((True for n in xrange(10) if str(n) in text))

        attempt, pkg_analyzer, journal_and_issue_data = item

        xml_tree = pkg_analyzer.xml

        funding_nodes = xml_tree.findall('.//funding-group')

        status, description = [models.Status.ok, etree.tostring(funding_nodes[0])] if funding_nodes != [] else [models.Status.warning, 'no funding-group']
        if status == models.Status.warning:
            ack_node = xml_tree.findall('.//ack')
            ack_text = etree.tostring(ack_node[0]) if ack_node != [] else ''

            if ack_text == '':
                description = 'no funding-group and no ack'
            elif _contains_number(ack_text):
                description = ack_text + ' looks to have contract number. If so, it must be identified using funding-group'
            else:
                description = ack_text
                status = models.Status.ok

        return [status, description]


class NLMJournalTitleValidationPipe(vpipes.ValidationPipe):
    """
    Validate NLM journal title
    """
    _stage_ = 'Journal'

    def __init__(self, notifier, pkg_analyzer, scieloapi, sapi_tools, normalize_data):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._normalize_data = normalize_data

    def validate(self, item):
        """
        Validate NLM journal title

        :param item: a tuple of (Attempt, PackageAnalyzer, journal_data)
        :returns: [models.Status.ok, nlm-journal-title], if nlm-journal-title in article and in journal match
        :returns: [models.Status.ok, ''], if journal has no nlm-journal-title
        :returns: [models.Status.error, nlm-journal-title in article and in journal], if nlm-journal-title in article and journal do not match.
        """
        attempt, pkg_analyzer, journal_and_issue_data = item

        j_nlm_title = journal_and_issue_data.get('journal').get('medline_title', '')
        if j_nlm_title == '':
            status, description = [models.Status.ok, 'journal has no NLM journal title']
        else:
            xml_tree = pkg_analyzer.xml
            xml_nlm_title = xml_tree.findtext('.//journal-meta/journal-id[@journal-id-type="nlm-ta"]')

            if xml_nlm_title:
                if self._normalize_data(xml_nlm_title) == self._normalize_data(j_nlm_title):
                    status, description = [models.Status.ok, xml_nlm_title]
                else:
                    status, description = [models.Status.error, j_nlm_title + ' [journal]\n' + xml_nlm_title + ' [article]']
            else:
                status, description = [models.Status.error, 'Missing .//journal-meta/journal-id[@journal-id-type="nlm-ta"] in article']
        return [status, description]


class DOIVAlidationPipe(vpipes.ValidationPipe):
    """
    Verify if exists DOI in XML and if it`s validated before the CrossRef
    """

    _stage_ = 'Article'

    def __init__(self, notifier, pkg_analyzer, doi_validator):
        self._notifier = notifier
        self._pkg_analyzer = pkg_analyzer
        self._doi_validator = doi_validator

    def validate(self, item):

        attempt, pkg_analyzer, journal_data = item

        doi_xml = pkg_analyzer.xml.find('.//article-id/[@pub-id-type="doi"]')

        if doi_xml is not None:
            if self._doi_validator(doi_xml.text):
                return [models.Status.ok, '']
            else:
                return [models.Status.warning, 'DOI is not valid']
        else:
            return [models.Status.warning, 'missing DOI in xml']


class ArticleSectionValidationPipe(vpipes.ValidationPipe):
    """
    Validate the article section
    Analyzed tag: ``.//article-categories/subj-group[@subj-group-type="heading"]/subject``
    """

    _stage_ = 'Article'

    def __init__(self, notifier, scieloapi, sapi_tools, pkg_analyzer, normalize_data):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._pkg_analyzer = pkg_analyzer
        self._normalize_data = normalize_data

    def validate(self, item):
        """
        Performs a validation to one `item` of data iterator.

        `item` is a tuple comprised of instances of models.Attempt, a
        checkin.PackageAnalyzer, a dict of journal data and a dict of issue.
        """
        attempt, pkg_analyzer, issue_data = item

        xml_tree = pkg_analyzer.xml
        xml_section = xml_tree.findtext('.//article-categories/subj-group[@subj-group-type="heading"]/subject')

        if xml_section:
            if self._is_a_registered_section_title(issue_data['sections'], xml_section):
                r = [models.Status.ok, xml_section]
            else:
                r = [models.Status.error, xml_section + ' is not registered as section in ' + issue_data.get('label')]
        else:
            r = [models.Status.warning, 'Missing .//article-categories/subj-group[@subj-group-type="heading"]/subject']
        return r

    def _is_a_registered_section_title(self, sections, section_title):
        """
        Return section titles of an issue
        """
        # issue_data['sections'][0]['titles'][0][0=idioma, 1=titulo]
        # no entanto, deveria ser
        # issue_data['sections'][0]['titles'][0][idioma] = titulo
        section_title = self._normalize_data(section_title)
        r = False
        for section in sections:
            r = any([True for lang, sectitle in section['titles'] if self._normalize_data(sectitle) == section_title])
            if r:
                break
        return r


class ArticleMetaPubDateValidationPipe(vpipes.ValidationPipe):
    """
    Validate the article section
    Analyzed tag: ``.//article-meta/pub-date``
    """

    _stage_ = 'Article'

    def __init__(self, notifier, scieloapi, sapi_tools, pkg_analyzer, normalize_data):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._pkg_analyzer = pkg_analyzer
        self._normalize_data = normalize_data

    def validate(self, item):
        """
        Performs a validation to one `item` of data iterator.

        `item` is a tuple comprised of instances of models.Attempt, a
        checkin.PackageAnalyzer, a dict of journal data and a dict of issue.
        """
        _months_ = {v: k for k, v in enumerate(calendar.month_abbr)}

        attempt, pkg_analyzer, issue_data = item

        xml_tree = pkg_analyzer.xml
        xml_data = xml_tree.findall('.//article-meta//pub-date')

        issue_publication_year = str(issue_data.get('publication_year'))
        issue_publication_start_month = str(issue_data.get('publication_start_month'))
        issue_publication_end_month = str(issue_data.get('publication_end_month'))

        unmatcheds = []
        matched = []
        start = '0'
        end = '0'

        for item in xml_data:
            year = item.findtext('year')
            month = item.findtext('month')
            season = item.findtext('season')
            if season:
                if '-' in season:
                    start, end = season.split('-')
                    start = str(_months_.get(start))
                    end = str(_months_.get(end))
            else:
                end = '0'
                start = str(int(month)) if month.isdigit() else str(int(_months_.get(month)))
            if year == issue_publication_year and start == issue_publication_start_month and end == issue_publication_end_month:
                matched = (year, start, end)
                break
            else:
                unmatcheds.append((year, start, end))

        if matched:
            year, start, end = matched
            r = [models.Status.ok, 'year: {0}\nstart: {1}\nend: {2}'.format(year, start, end)]
        else:
            description = ''
            for year, start, end in unmatcheds:
                description += 'year: {0}\nstart: {1}\nend: {2}'.format(year, start, end) + '\n'

            r = [models.Status.error, 'Unmatched publication date.\nIn article:\n' + description + 'In   issue: \n' + 'year: {0}\nstart: {1}\nend: {2}'.format(issue_publication_year, issue_publication_start_month, issue_publication_end_month) + '\n']
        return r


if __name__ == '__main__':
    utils.setup_logging()
    config = utils.Configuration.from_env()

    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    scieloapi = scieloapi.Client(config.get('manager', 'api_username'),
                                 config.get('manager', 'api_key'))

    notifier_dep = notifier.validation_notifier_factory(config)

    ppl = vpipes.Pipeline(
        SetupPipe(notifier_dep, scieloapi, scieloapitoolbelt,
            checkin.PackageAnalyzer, utils.is_valid_issn),
        PublisherNameValidationPipe(notifier_dep, scieloapi, scieloapitoolbelt,
            checkin.PackageAnalyzer, utils.normalize_data),
        JournalAbbreviatedTitleValidationPipe(notifier_dep, checkin.PackageAnalyzer,
            scieloapi, utils.normalize_data),
        NLMJournalTitleValidationPipe(notifier_dep, checkin.PackageAnalyzer,
            scieloapi, scieloapitoolbelt, utils.normalize_data),
        ArticleSectionValidationPipe(notifier_dep, scieloapi, scieloapitoolbelt,
            checkin.PackageAnalyzer, utils.normalize_data),
        FundingGroupValidationPipe(notifier_dep, checkin.PackageAnalyzer),
        DOIVAlidationPipe(notifier_dep, checkin.PackageAnalyzer, utils.is_valid_doi),
        ArticleMetaPubDateValidationPipe(notifier_dep, scieloapi, scieloapitoolbelt,
            checkin.PackageAnalyzer, utils.normalize_data),
        ReferenceValidationPipe(notifier_dep, checkin.PackageAnalyzer),
        ReferenceSourceValidationPipe(notifier_dep, checkin.PackageAnalyzer),
        ReferenceJournalTypeArticleTitleValidationPipe(notifier_dep,
            checkin.PackageAnalyzer),
        ReferenceYearValidationPipe(notifier_dep, checkin.PackageAnalyzer),
        TearDownPipe(notifier_dep, scieloapi, scieloapitoolbelt,
            checkin.PackageAnalyzer)
    )

    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
