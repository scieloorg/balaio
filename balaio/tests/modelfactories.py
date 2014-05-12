"""
Factories produce real instances of the objects they refer to.

Usually, factories are used to produce database-bound object
instances, declared in the `lib.models.py` module.

Sacred commandments:

* It is desirable to respect the default values set by the instance's
__init__ method, so they should be left undefined.

* If an attribute is nullable, its value should be None.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory

from balaio.lib import models


class ArticlePkgFactory(SQLAlchemyModelFactory):
    """
    Example of valid ISSN: 0100-879X
    """
    FACTORY_FOR = models.ArticlePkg
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    aid = factory.Sequence(lambda n: 'as36%s' % n)
    article_title = 'Construction of a recombinant adenovirus...'
    journal_pissn = None
    journal_eissn = None
    journal_title = 'Associa... Brasileira'
    issue_year = 1995
    issue_volume = None
    issue_number = None
    issue_suppl_volume = None
    issue_suppl_number = None


class AttemptFactory(SQLAlchemyModelFactory):
    """
    These should be left undefined:
    started_at, is_valid, proceed_to_validation, proceed_to_checkout.
    """
    FACTORY_FOR = models.Attempt
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    package_checksum = factory.Sequence(lambda n: '20132df0as89dds73as936%s' % n)
    articlepkg = factory.SubFactory(ArticlePkgFactory)
    finished_at = None
    filepath = '/tmp/watch/xxx.zip'
    checkin_uri = None
    validation_started_at = None
    validation_ended_at = None
    checkout_started_at = None
    queued_checkout = None


class CheckpointFactory(SQLAlchemyModelFactory):
    """
    These should be left undefined:
    _point, started_at, ended_at.
    """
    FACTORY_FOR = models.Checkpoint
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    point = models.Point.checkin
    attempt = factory.SubFactory(AttemptFactory)

