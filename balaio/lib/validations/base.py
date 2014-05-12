#coding: utf-8
"""Base functionality for the validation pipeline."""

__all__ = ['attempt_is_valid',
           'ValidationPipe',
           'SetupPipe',
           'TearDownPipe',
           ]

import logging

import transaction
import plumber

from .. import (
    utils,
    package,
    notifier,
    models,
)


logger = logging.getLogger(__name__)


def attempt_is_valid(data):
    """
    Ensure the `models.Attempt` instance is valid before being processed.

    This function is for use as a precondition. See:
    http://git.io/kPMqqw
    """
    try:
        attempt, _, _, _ = data
    except TypeError:
        attempt = data

    if attempt.is_valid != True:
        logger.debug('Attempt %s does not comply the precondition to be processed by the pipe. Bypassing.' % repr(attempt))
        raise plumber.UnmetPrecondition()


class ValidationPipe(plumber.Pipe):

    """
    Specialized Pipe which validates the data and notifies the result.
    """
    def __init__(self, notifier):
        self._notifier = notifier

    @plumber.precondition(attempt_is_valid)
    def transform(self, item):
        """
        Performs a transformation to one `item` of data iterator.

        `item` is a tuple comprised of instances of models.Attempt, a
        checkin.PackageAnalyzer, a dict of journal and issue data.
        """
        attempt = item[0]
        db_session = item[3]
        logger.debug('%s started processing %s' % (self.__class__.__name__, attempt))

        result_status, result_description = self.validate(item)

        savepoint = transaction.savepoint()
        try:
            self._notifier(attempt, db_session).tell(result_description, result_status, label=self._stage_)
        except Exception as e:
            savepoint.rollback()
            logger.error('An exception was raised during %s stage: %s' % (self._stage_, e))
            raise

        return item

    def validate(self, item):
        """
        Performs the validation of `item`.

        `item` is a tuple comprised of instances of models.Attempt, a
        checkin.PackageAnalyzer, a dict of journal and issue data.
        """
        raise NotImplementedError()


#------------------------------------------------------------------------------
# First and last pipes to run at the validation pipeline.
#------------------------------------------------------------------------------
class SetupPipe(plumber.Pipe):

    def __init__(self, notifier, scieloapi, sapi_tools, pkg_analyzer, issn_validator):
        self._notifier = notifier
        self._scieloapi = scieloapi
        self._sapi_tools = sapi_tools
        self._pkg_analyzer = pkg_analyzer
        self._issn_validator = issn_validator

    def _fetch_journal_and_issue_data(self, **criteria):
        """
        Encapsulates the two-phase process of retrieving
        data from one issue matching the criteria and then
        its related journal.

        :param criteria: valid criteria to retrieve issue data
        """
        issues = self._scieloapi.issues.filter(limit=1, **criteria)

        try:
            issue = self._sapi_tools.get_one(issues)
        except ValueError:
            # dataset is empty
            return None

        return self._scieloapi.fetch_relations(issue)

    def get_journal(self, attempt):
        """
        Retrieve remote data from SciELO Manager about the issue the
        attempt is related.
        """
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
        journal_eissn = attempt.articlepkg.journal_eissn
        journal_and_issue_data = None

        # first, try to get the content by the print issn.
        if journal_pissn and self._issn_validator(journal_pissn):
            journal_and_issue_data = self._fetch_journal_and_issue_data(
                print_issn=journal_pissn, **criteria)

        # if something went wrong, try the electronic issn
        if not journal_and_issue_data and (journal_eissn and
            self._issn_validator(journal_eissn)):

            journal_and_issue_data = self._fetch_journal_and_issue_data(
                eletronic_issn=journal_eissn, **criteria)

        return journal_and_issue_data

    def transform(self, message):
        """
        Adds some data that will be needed during validation
        workflow.

        :param message: is a models.Attempt, db session pair.
        :returns: a tuple (Attempt, PackageAnalyzer, journal_data, db_session)
        """
        # setup
        attempt, db_session = message
        notifier = self._notifier(attempt, db_session)

        logger.debug('%s started processing %s' % (self.__class__.__name__, attempt))

        attempt.start_validation()
        notifier.start()

        # retrieving the zip package inspection object,
        # and making sure it is locked during the operation.
        pkg_analyzer = attempt.analyzer
        pkg_analyzer.lock_package()

        journal_data = self.get_journal(attempt)
        if not journal_data:
            logger.info('%s is not related to a known journal' % attempt)

            # mark the attempt as invalid and notify SciELO Manager
            attempt.is_valid = False
            notifier.tell('The article is not related to a known journal or issue.',
                models.Status.error)

        return (attempt, pkg_analyzer, journal_data, db_session)


class TearDownPipe(plumber.Pipe):
    def __init__(self, notifier):
        self._notifier = notifier

    def transform(self, item):
        attempt, pkg_analyzer, journal, db_session = item

        logger.debug('%s started processing %s' % (self.__class__.__name__, item))
        self._notifier(attempt, db_session).end()

        pkg_analyzer.restore_perms()

        if not attempt.is_valid:
            utils.mark_as_failed(attempt.filepath)

        attempt.end_validation()
        logger.info('Finished validating %s' % attempt)

