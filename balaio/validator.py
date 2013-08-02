# coding: utf-8
import sys
import logging

import scieloapi

import vpipes
import utils
import notifier
import checkin
import scieloapitoolbelt
import models


logger = logging.getLogger('balaio.validator')

STATUS_OK = 'ok'
STATUS_WARNING = 'warning'
STATUS_ERROR = 'error'


class SetupPipe(vpipes.ConfigMixin, vpipes.Pipe):
    __requires__ = ['_notifier', '_scieloapi', '_sapi_tools', '_pkg_analyzer', '_issn_validator']

    def _fetch_journal_data(self, criteria):
        """
        Encapsulates the two-phase process of retrieving
        data from one journal matching the criteria.
        """
        found_journals = self._scieloapi.journals.filter(
            limit=1, **criteria)
        return self._sapi_tools.get_one(found_journals)

    def transform(self, attempt):
        """
        Adds some data that will be needed during validation
        workflow.

        `attempt` is an models.Attempt instance.
        """
        logger.debug('%s started processing %s' % (self.__class__.__name__, attempt))

        pkg_analyzer = self._pkg_analyzer(attempt.filepath)
        pkg_analyzer.lock_package()

        journal_pissn = attempt.articlepkg.journal_pissn

        if journal_pissn and self._issn_validator(journal_pissn):
            try:
                journal_data = self._fetch_journal_data(
                    {'print_issn': journal_pissn})
            except ValueError:
                # unknown pissn
                journal_data = None

        journal_eissn = attempt.articlepkg.journal_eissn
        if journal_eissn and self._issn_validator(journal_eissn) and not journal_data:
            try:
                journal_data = self._fetch_journal_data(
                    {'eletronic_issn': journal_eissn})
            except ValueError:
                # unknown eissn
                journal_data = None

        if not journal_data:
            logger.info('%s is not related to a known journal' % attempt)
            attempt.is_valid = False

        return_value = (attempt, pkg_analyzer, journal_data)
        logger.debug('%s returning %s' % (self.__class__.__name__, ','.join([repr(val) for val in return_value])))
        return return_value


class TearDownPipe(vpipes.ConfigMixin, vpipes.Pipe):
    __requires__ = ['_notifier', '_scieloapi', '_sapi_tools', '_pkg_analyzer']

    def transform(self, item):
        logger.debug('%s started processing %s' % (self.__class__.__name__, item))
        attempt, pkg_analyzer, journal_data = item

        pkg_analyzer.restore_perms()

        if attempt.is_valid:
            logger.info('Finished validating %s' % attempt)
        else:
            utils.mark_as_failed(attempt.filepath)
            logger.info('%s is invalid. Finished.' % attempt)


if __name__ == '__main__':
    utils.setup_logging()
    config = utils.Configuration.from_env()

    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    scieloapi = scieloapi.Client(config.get('manager', 'api_username'),
                                 config.get('manager', 'api_key'))
    notifier_dep = notifier.Notifier()

    ppl = vpipes.Pipeline(SetupPipe, TearDownPipe)

    # add all dependencies to a registry-ish thing
    ppl.configure(_scieloapi=scieloapi,
                  _notifier=notifier_dep,
                  _sapi_tools=scieloapitoolbelt,
                  _pkg_analyzer=checkin.PackageAnalyzer,
                  _issn_validator=utils.is_valid_issn)

    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)

