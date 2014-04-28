# coding: utf-8
"""Validations related to the Journal metadata."""

__all__ = ['ReferenceValidationPipe',
           'ReferenceSourceValidationPipe',
           'ReferenceYearValidationPipe',
           'ReferenceJournalTypeArticleTitleValidationPipe',
           ]

import re
import logging

from .. import models
from . import base


logger = logging.getLogger(__name__)


class ReferenceValidationPipe(base.ValidationPipe):
    """
    Validate if exist the tag ref-list.
    Analyzed tag: ``.//ref-list/ref``
    """
    _stage_ = 'References'

    def __init__(self, notifier):
        self._notifier = notifier

    def validate(self, item):
        """
        The article may be a editorial why return a warning if no references
        """
        attempt, pkg_analyzer, journal_and_issue_data = item[:3]
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            return [models.Status.ok, 'Found ' + str(len(refs)) + ' references']
        else:
            return [models.Status.warning, 'Missing data: references']


class ReferenceSourceValidationPipe(base.ValidationPipe):
    """
    Validate the tag source references
    Verify if exists tag source references
    Verify if exists content in tag source
    Analized tag: ``.//ref-list/ref/element-citation/source``
    """
    _stage_ = 'References'

    def __init__(self, notifier):
        self._notifier = notifier

    def validate(self, item):
        lst_errors = []
        attempt, pkg_analyzer, journal_and_issue_data = item[:3]
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            for ref in refs:
                source = ref.find(".//source")

                if source is not None:
                    if source.text is None:
                        lst_errors.append(ref.attrib['id'])
                else:
                    lst_errors.append(ref.attrib['id'])

        if lst_errors:
            msg_error = 'Missing data: source. (%s)' % ', '.join(lst_errors)

        return [models.Status.error, msg_error] if lst_errors else [models.Status.ok, 'Valid data: source']


class ReferenceYearValidationPipe(base.ValidationPipe):
    """
    Validate the tag year references
    Verify if exists tag year references
    Verify if exists content in tag year
    Verify the format of the year, example: ``1999``
    Analized tag: ``.//ref-list/ref/element-citation/year``
    """
    _stage_ = 'References'

    def __init__(self, notifier):
        self._notifier = notifier

    def validate(self, item):

        missing_data_ref_id_list = []
        bad_data = []

        attempt, pkg_analyzer, journal_and_issue_data = item[:3]
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            for ref in refs:
                year = ref.find(".//year")

                if year is not None:
                    if year.text is None:
                        missing_data_ref_id_list.append(ref.attrib['id'])
                    else:
                        if not re.search(r'\d{4}', year.text):
                            bad_data.append((ref.attrib['id'], year.text))
                else:
                    missing_data_ref_id_list.append(ref.attrib['id'])

        msg_error = ''
        if missing_data_ref_id_list:
            msg_error = 'Missing data: year. (%s)' % ', '.join(missing_data_ref_id_list)

        if bad_data:
            if msg_error:
                msg_error += '. '
            msg_error += 'Invalid value for year: %s' % ', '.join(['%s (%s)' % (year, ref) for ref, year in bad_data])

        return [models.Status.error, msg_error] if msg_error else [models.Status.ok, 'Valid data: year']


class ReferenceJournalTypeArticleTitleValidationPipe(base.ValidationPipe):
    """
    Validate the tag article-title references when type is Journal.
    Analized tag: ``.//ref-list/ref/element-citation[@publication-type='journal']/article-title``
    """
    _stage_ = 'References'

    def __init__(self, notifier):
        self._notifier = notifier

    def validate(self, item):

        lst_errors = []

        attempt, pkg_analyzer, journal_and_issue_data = item[:3]
        refs = pkg_analyzer.xml.findall(".//ref-list/ref")

        if refs:
            for ref in refs:
                article_title = ref.find(".//element-citation[@publication-type='journal']/article-title")

                if article_title is not None:
                    if article_title.text is None:
                        lst_errors.append(ref.attrib['id'])
                else:
                    lst_errors.append(ref.attrib['id'])

        return [models.Status.error, 'Missing data: article-title. (%s)' % ', '.join(lst_errors) ] if lst_errors else [models.Status.ok, 'Valid data: article-title']

