# coding: utf-8
"""Validations related to the Journal metadata."""

__all__ = ['PublisherNameValidationPipe',
           'JournalAbbreviatedTitleValidationPipe',
           'NLMJournalTitleValidationPipe',
           ]


import logging

from .. import models
from . import base


logger = logging.getLogger(__name__)


class PublisherNameValidationPipe(base.ValidationPipe):
    """
    Validate the publisher name in article `.//journal-meta/publisher/publisher-name`,
    comparing it to the registered publisher name in journal data.
    """
    _stage_ = 'Journal'

    def __init__(self, notifier, normalize_data):
        self._normalize_data = normalize_data
        self._notifier = notifier

    def validate(self, item):
        """
        Performs a validation to one `item` of data iterator.

        :param item: a tuple (models.Attempt, package.PackageAnalyzer, a dict of journal issue data).
        :returns: result of the validation in this format [status, description]
        """
        attempt, pkg_analyzer, journal_and_issue_data = item[:3]
        j_publisher_name = journal_and_issue_data.get('journal', {}).get('publisher_name', None)
        if j_publisher_name:
            data = pkg_analyzer.xml
            xml_publisher_name = data.findtext('.//journal-meta/publisher/publisher-name')

            if xml_publisher_name:
                if self._normalize_data(xml_publisher_name) == self._normalize_data(j_publisher_name):
                    r = [models.Status.ok, 'Valid publisher name: ' + xml_publisher_name]
                else:
                    r = [models.Status.error, 'Mismatched data: %s. Expected: %s' % (xml_publisher_name, j_publisher_name)]
            else:
                r = [models.Status.error, 'Missing data: publisher name']
        else:
            r = [models.Status.error, 'Missing data: publisher name, in scieloapi']
        return r


class JournalAbbreviatedTitleValidationPipe(base.ValidationPipe):
    """
    Checks exist abbreviated title on source and xml
    Verify if abbreviated title of the xml is equal to source
    """
    _stage_ = 'Journal'

    def __init__(self, notifier, normalize_data):
        self._notifier = notifier
        self._normalize_data = normalize_data

    def validate(self, item):

        attempt, pkg_analyzer, journal_and_issue_data = item[:3]
        abbrev_title = journal_and_issue_data.get('journal').get('short_title')

        if abbrev_title:
            abbrev_title_xml = pkg_analyzer.xml.find('.//journal-meta/journal-title-group/abbrev-journal-title[@abbrev-type="publisher"]')
            if abbrev_title_xml is not None:
                if self._normalize_data(abbrev_title) == self._normalize_data(abbrev_title_xml.text):
                    return [models.Status.ok, 'Valid abbrev-journal-title: %s' % abbrev_title_xml.text ]
                else:
                    return [models.Status.error, 'Mismatched data: %s. Expected: %s' % (abbrev_title_xml.text, abbrev_title)]
            else:
                return [models.Status.error, 'Missing data: abbrev-journal-title']
        else:
            return [models.Status.error, 'Missing data: short_title, in scieloapi']


class NLMJournalTitleValidationPipe(base.ValidationPipe):
    """
    Validate NLM journal title
    """
    _stage_ = 'Journal'

    def __init__(self, notifier, normalize_data):
        self._notifier = notifier
        self._normalize_data = normalize_data

    def validate(self, item):
        """
        Validate NLM journal title

        :param item: a tuple of (Attempt, PackageAnalyzer, journal_data)
        :returns: [models.Status.ok, nlm-journal-title], if nlm-journal-title in article and in journal match
        :returns: [models.Status.ok, ''], if journal has no nlm-journal-title
        :returns: [models.Status.error, nlm-journal-title in article and in journal], if nlm-journal-title in article and journal do not match.
        """
        attempt, pkg_analyzer, journal_and_issue_data = item[:3]

        #The value returned from get('medline_title') when do not have title is None
        j_nlm_title = journal_and_issue_data.get('journal').get('medline_title')

        xml_tree = pkg_analyzer.xml
        xml_nlm_title = xml_tree.findtext('.//journal-meta/journal-id[@journal-id-type="nlm-ta"]')

        if not xml_nlm_title:
            xml_nlm_title = ''

        if not j_nlm_title:
            j_nlm_title = ''

        if self._normalize_data(xml_nlm_title) == self._normalize_data(j_nlm_title):
            status, description = [models.Status.ok, 'Valid NLM journal title: %s' % xml_nlm_title]
        else:
            status, description = [models.Status.error, 'Mismatched data: %s. Expected: %s' % (xml_nlm_title, j_nlm_title)]

        return [status, description]

