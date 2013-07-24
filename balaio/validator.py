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


class SetupPipe(vpipes.Pipe):
    def __init__(self,
                 data,
                 scieloapi=None,
                 notifier_dep=None,
                 scieloapitools_dep=scieloapitoolbelt,
                 pkganalyzer_dep=checkin.PackageAnalyzer):
        """
        `data` is an iterable that will pass thru the pipe.
        `scieloapi` is an instance of scieloapi.Client.
        """
        super(SetupPipe, self).__init__(data)

        self._pkg_analyzer = pkganalyzer_dep
        self._sapi_tools = scieloapitools_dep
        if scieloapi:
            self._scieloapi = scieloapi
        else:
            raise ValueError('missing argument scieloapi')
        self._issn_validator = utils.is_valid_issn

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
            # the package is not related to a known journal
            # at least by its [ep]ISSN.
            pass


        return (attempt, pkg_analyzer, journal_data)


class TearDownPipe(vpipes.Pipe):
    pass


class PISSNValidationPipe(vpipes.ValidationPipe):
    """
    Verify if PISSN exists on SciELO Manager and if it's valid.

    PISSN should not be mandatory, since SciELO is an electronic
    library online.
    If a PISSN is invalid, a warning is raised instead of an error.
    The analyzed atribute is ``.//issn[@pub-type="ppub"]``
    """
    _stage_ = 'issn'

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        pissn = data.findtext(".//issn[@pub-type='ppub']")

        if not pissn:
            return [STATUS_OK, '']
        elif utils.is_valid_issn(pissn):
            # check if the pissn is from a known journal
            remote_journals = self._scieloapi.journals.filter(
                print_issn=pissn, limit=1)

            if self._sapi_tools.has_any(remote_journals):
                return [STATUS_OK, '']

        return [STATUS_WARNING, 'print ISSN is invalid or unknown']


class EISSNValidationPipe(vpipes.ValidationPipe):
    """
    Verify if EISSN exists on SciELO Manager and if it's valid.

    The analyzed atribute is ``.//issn/@pub-type="epub"``
    """
    _stage_ = 'issn'

    def validate(self, package_analyzer):

        data = package_analyzer.xml

        eissn = data.findtext(".//issn[@pub-type='epub']")

        if eissn and utils.is_valid_issn(eissn):
            remote_journals = self._scieloapi.journals.filter(
                eletronic_issn=eissn, limit=1)

            if self._sapi_tools.has_any(remote_journals):
                return [STATUS_OK, '']

        return [STATUS_ERROR, 'electronic ISSN is invalid or unknown']


if __name__ == '__main__':
    utils.setup_logging()
    config = utils.Configuration.from_env()

    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    scieloapi = scieloapi.Client(config.get('manager', 'api_username'),
                                 config.get('manager', 'api_key'))
    notifier_dep = notifier.Notifier()

    pipes = [
        SetupPipe,
        #PISSNValidationPipe,
        #EISSNValidationPipe,
    ]
    ppl = vpipes.Pipeline(*pipes)
    ppl.configure(scieloapi, notifier_dep)

    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)

