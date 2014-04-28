# coding: utf-8
"""Validations related to the Article metadata."""

__all__ = ['FundingGroupValidationPipe',
           'DOIVAlidationPipe',
           'LicenseValidationPipe',
           'ArticleSectionValidationPipe',
           'ArticleMetaPubDateValidationPipe',
           ]

import logging
import xml.etree.ElementTree as etree
import calendar

from .. import models
from . import base


logger = logging.getLogger(__name__)


class FundingGroupValidationPipe(base.ValidationPipe):
    """
    Validate Funding Group according to the following rules:
    Funding group is mandatory only if there is contract number in the article,
    and this data is usually in acknowledge
    """
    _stage_ = 'Article'

    def __init__(self, notifier):
        self._notifier = notifier

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

        attempt, pkg_analyzer, journal_and_issue_data = item[:3]

        xml_tree = pkg_analyzer.xml

        funding_nodes = xml_tree.findall('.//funding-group')

        status, description = [models.Status.ok, etree.tostring(funding_nodes[0])] if funding_nodes != [] else [models.Status.warning, 'Missing data: funding-group']
        if status == models.Status.warning:
            ack_node = xml_tree.findall('.//ack')
            ack_text = etree.tostring(ack_node[0]) if ack_node != [] else ''

            if ack_text == '':
                description = 'Missing data: funding-group, ack'
            elif _contains_number(ack_text):
                description = '%s has numbers. If it is a contract number, it must be identified in funding-group.' % ack_text
            else:
                description = ack_text
                status = models.Status.ok

        return [status, description]


class DOIVAlidationPipe(base.ValidationPipe):
    """
    Verify if exists DOI in XML and if it`s validated before the CrossRef
    """

    _stage_ = 'Article'

    def __init__(self, notifier, doi_validator):
        self._notifier = notifier
        self._doi_validator = doi_validator

    def validate(self, item):

        attempt, pkg_analyzer, journal_data = item[:3]

        doi_xml = pkg_analyzer.xml.findtext('.//article-id/[@pub-id-type="doi"]')

        if doi_xml:
            if self._doi_validator(doi_xml):
                return [models.Status.ok, 'Valid DOI: %s' % doi_xml]
            else:
                return [models.Status.warning, 'DOI is not registered: %s' % doi_xml]
        else:
            return [models.Status.warning, 'Missing data: DOI']


class LicenseValidationPipe(base.ValidationPipe):
    """
    Verify if exists license in XML
    Analyzed tag: ``.//article-meta/permissions/license/license-p``
    """

    _stage_ = 'Article'

    def __init__(self, notifier):
        self._notifier = notifier

    def validate(self, item):

        attempt, pkg_analyzer, journal_data = item[:3]

        license_xml = pkg_analyzer.xml.find('.//article-meta/permissions')

        if license_xml is not None:
            if license_xml.findtext('.//license-p'):
                return [models.Status.ok, 'This article have a valid license']
            else:
                return [models.Status.warning, 'This article dont have a license']
        else:
            return [models.Status.error, 'Missing data: permissions']


class ArticleSectionValidationPipe(base.ValidationPipe):
    """
    Validate the article section
    Analyzed tag: ``.//article-categories/subj-group[@subj-group-type="heading"]/subject``
    """

    _stage_ = 'Article'

    def __init__(self, notifier, normalize_data):
        self._notifier = notifier
        self._normalize_data = normalize_data

    def validate(self, item):
        """
        Performs a validation to one `item` of data iterator.

        `item` is a tuple comprised of instances of models.Attempt, a
        package.PackageAnalyzer, a dict of journal data and a dict of issue.
        """
        attempt, pkg_analyzer, issue_data = item[:3]

        xml_tree = pkg_analyzer.xml
        xml_section = xml_tree.findtext('.//article-categories/subj-group[@subj-group-type="heading"]/subject')

        if xml_section:
            if self._is_a_registered_section_title(issue_data['sections'], xml_section):
                r = [models.Status.ok, 'Valid article section: %s' % xml_section]
            else:
                r = [models.Status.error, 'Mismatched data: %s. Expected one of %s' % (xml_section, self.list_sections(issue_data['sections']))]
        else:
            r = [models.Status.warning, 'Missing data: article section']
        return r

    def _is_a_registered_section_title(self, sections, section_title):
        """
        Return section titles of an issue

        :param sections: has the structure:
                [ {'titles':
                    ['pt', 'Artigos Originais'],
                    ['es', 'Articulos Originales'],
                    ['en', 'Original Articles'],
                  },
                  {'titles':
                    ['pt', 'Editorial'],
                    ['es', 'Editorial'],
                    ['en', 'Editorial'],
                  },
                ]
        """
        section_title = self._normalize_data(section_title)
        r = False
        for section in sections:
            r = any([True for lang, sectitle in section['titles'] if self._normalize_data(sectitle) == section_title])
            if r:
                break
        return r

    def list_sections(self, sections):
        """
        Return section titles of an issue
        """
        # issue_data['sections'][0]['titles'][0][0=idioma, 1=titulo]
        # no entanto, deveria ser
        # issue_data['sections'][0]['titles'][0][idioma] = titulo
        titles = []
        for section in sections:
            for lang, sectitle in section['titles']:
                titles.append(sectitle)
        return ' | '.join(titles)


class ArticleMetaPubDateValidationPipe(base.ValidationPipe):
    """
    Validate the article section
    Analyzed tag: ``.//article-meta/pub-date``
    """

    _stage_ = 'Article'

    def __init__(self, notifier):
        self._notifier = notifier

    def validate(self, item):
        """
        Performs a validation to one `item` of data iterator.

        `item` is a tuple comprised of instances of models.Attempt, a
        package.PackageAnalyzer, a dict of journal data and a dict of issue.
        """
        _months_by_name = {v: k for k, v in enumerate(calendar.month_abbr)}
        _month_abbrev_name = {k: v for k, v in enumerate(calendar.month_abbr)}

        attempt, pkg_analyzer, issue_data = item[:3]

        xml_tree = pkg_analyzer.xml
        xml_data = xml_tree.findall('.//article-meta//pub-date')

        issue_year = str(issue_data.get('publication_year'))
        issue_start_month_name = _month_abbrev_name.get(issue_data.get('publication_start_month'))
        issue_end_month_name = _month_abbrev_name.get(issue_data.get('publication_end_month'))
        issue_start_month_num = str(issue_data.get('publication_start_month'))
        issue_end_month_num = str(issue_data.get('publication_end_month'))

        expected = []
        if issue_end_month_num == '0':
            expected.append('%s/%s' % (issue_start_month_name, issue_year))
            expected.append('%s/%s' % (issue_start_month_num, issue_year))
        else:
            expected.append('%s-%s/%s' % (issue_start_month_name, issue_end_month_name, issue_year))
            expected.append('%s-%s/%s' % (issue_start_month_num, issue_end_month_name, issue_year))

        unmatched = []
        r = None
        for item in xml_data:
            year = item.findtext('year')
            month = item.findtext('month')
            season = item.findtext('season')
            if season:
                xml_date = '%s/%s' % (season, year)
            else:
                xml_date = '%s/%s' % ((str(int(month)), year) if month.isdigit() else (month, year))

            if xml_date in expected:
                return [models.Status.ok, 'Valid publication date: %s' % xml_date]
            else:
                unmatched.append(xml_date)

        return [models.Status.error, 'Mismatched data: %s. Expected one of %s' % (' | '.join(unmatched), ' | '.join(expected))]

