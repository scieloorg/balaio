import factory
from factory.alchemy import SQLAlchemyModelFactory

from balaio import models

class ArticlePkgFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = models.ArticlePkg
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    aid = factory.Sequence(lambda n: 'as36%s' % n)
    article_title = 'Construction of a recombinant adenovirus...'
    journal_pissn = '0100-879X'
    journal_eissn = '0100-879X'
    journal_title = 'Associa... Brasileira'
    issue_year = 1995
    issue_volume = '67'
    issue_number = '8'
    issue_suppl_volume = None
    issue_suppl_number = None


class AttemptFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = models.Attempt
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    package_checksum = factory.Sequence(lambda n: '20132df0as89dds73as936%s' % n)
    finished_at = None
    collection_uri = ''
    articlepkg = factory.SubFactory(ArticlePkgFactory)
    filepath = '/tmp/watch/xxx.zip'


class TicketFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = models.Ticket
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    title = "Erro no pacote xxx"
    author = 'Aberlado Barbosa'
    articlepkg = factory.SubFactory(ArticlePkgFactory)


class CheckpointFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = models.Checkpoint
    FACTORY_SESSION = models.ScopedSession

    id = factory.Sequence(lambda n: n)
    point = models.Point.checkin
    attempt = factory.SubFactory(AttemptFactory)

