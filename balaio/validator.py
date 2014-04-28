# coding: utf-8
import sys
import logging
import time

import scieloapi
import transaction
import plumber

from lib import (
    utils,
    package,
    notifier,
    scieloapitoolbelt,
    models,
    validations,
)


logger = logging.getLogger('balaio.validator')


class Worker(object):

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def _load_messages(self, session):
        messages = session.query(models.Attempt).filter(
            models.Attempt.ready_to_validate())

        return messages

    def run_once(self):
        logger.debug('New validation round.')
        session = models.Session()

        raw_messages = self._load_messages(session)

        # check if there is something to do.
        # if not, close the session and return.
        if not raw_messages.first():
            transaction.abort()
            session.close()
            logger.debug('End of validation round. Nothing to do.')
            return None

        try:
            # enrich each message with the current session.
            messages = ((msg, session) for msg in raw_messages)

            for _ in self.pipeline.run(messages):
                # nothing to do here.
                pass
        finally:

            try:
                transaction.commit()
            except Exception as e:
                logger.error(e.message)
                transaction.abort()
            finally:
                session.close()
                logger.debug('End of validation round.')

    def start(self):
        while True:
            self.run_once()
            time.sleep(10)


if __name__ == '__main__':
    # App bootstrapping:
    # Setting up the app configuration, logging and SqlAlchemy Session.
    config = utils.balaio_config_from_env()
    utils.setup_logging(config)
    models.Session.configure(bind=models.create_engine_from_config(config))

    # Setting up some pipe dependencies.
    scieloapi = scieloapi.Client(config.get('manager', 'api_username'),
                                 config.get('manager', 'api_key'),
                                 api_uri=config.get('manager', 'api_url'))

    notifier_dep = notifier.validation_notifier_factory(config)

    ppl = plumber.Pipeline(
        # SetupPipe must always be the first pipe.
        validations.SetupPipe(notifier_dep, scieloapi, scieloapitoolbelt,
                              package.PackageAnalyzer, utils.is_valid_issn),

        # Journal group
        validations.PublisherNameValidationPipe(notifier_dep, utils.normalize_data),
        validations.JournalAbbreviatedTitleValidationPipe(notifier_dep, utils.normalize_data),
        validations.NLMJournalTitleValidationPipe(notifier_dep, utils.normalize_data),

        # Article group
        validations.ArticleSectionValidationPipe(notifier_dep, utils.normalize_data),
        validations.FundingGroupValidationPipe(notifier_dep),
        validations.DOIVAlidationPipe(notifier_dep, utils.is_valid_doi),
        validations.ArticleMetaPubDateValidationPipe(notifier_dep),
        #validations.LicenseValidationPipe(notifier_dep),

        # References group
        validations.ReferenceValidationPipe(notifier_dep),
        validations.ReferenceSourceValidationPipe(notifier_dep),
        validations.ReferenceJournalTypeArticleTitleValidationPipe(notifier_dep),
        validations.ReferenceYearValidationPipe(notifier_dep),

        # TearDownPipe must always be the last pipe.
        validations.TearDownPipe(notifier_dep)
    )

    while True:
        try:
            app = Worker(ppl)
            app.start()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            logger.error(e.message)

