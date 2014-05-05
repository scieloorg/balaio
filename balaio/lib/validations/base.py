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

    def _fetch_journal_data(self, criteria):
        """
        Encapsulates the two-phase process of retrieving
        data from one journal matching the criteria.

        :param criteria: valid criteria to retrieve journal data
        :returns: data of one journal
        """
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
        found_journal_issues = self._scieloapi.issues.filter(
            limit=1, **criteria)
        return self._scieloapi.fetch_relations(self._sapi_tools.get_one(found_journal_issues))

    def transform(self, message):
        """
        Adds some data that will be needed during validation
        workflow.

        :param message: is a models.Attempt, db session pair.
        :returns: a tuple (Attempt, PackageAnalyzer, journal_and_issue_data, db_session)
        """
        # setup
        attempt, db_session = message
        attempt.start_validation()

        logger.debug('%s started processing %s' % (self.__class__.__name__, attempt))
        self._notifier(attempt, db_session).start()

        # retrieving the zip package inspection object,
        # and making sure it is locked during the operation.
        pkg_analyzer = attempt.analyzer
        pkg_analyzer.lock_package()

        # retrieving remote data from SciELO Manager
        # about the issue the attempt's article refers.
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
            repr_err_msg = '%s is not related to a known journal' % attempt
            err_msg = 'The article is not related to a known journal or issue.'
            logger.info(repr_err_msg)

            # mark the attempt as invalid and notify SciELO Manager
            attempt.is_valid = False
            self._notifier(attempt, db_session).tell(err_msg, models.Status.error)

        # producing the response tuple that will traverse all pipes.
        return_value = (attempt, pkg_analyzer, journal_and_issue_data, db_session)
        logger.debug('%s returning %s' % (self.__class__.__name__, ','.join([repr(val) for val in return_value])))

        return return_value


class TearDownPipe(plumber.Pipe):
    def __init__(self, notifier):
        self._notifier = notifier

    def transform(self, item):
        """
        :param item:
        """
        attempt, pkg_analyzer, __, db_session = item

        logger.debug('%s started processing %s' % (self.__class__.__name__, item))

        try:
            self._notifier(attempt, db_session).end()
        except RuntimeError:
            pass

        if 'pkg_analyzer' in locals():
            pkg_analyzer.restore_perms()

        if not attempt.is_valid:
            utils.mark_as_failed(attempt.filepath)

        attempt.end_validation()

        logger.info('Finished validating %s' % attempt)

