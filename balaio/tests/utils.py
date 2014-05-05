from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from balaio.lib import models


DB_NAME = 'app_balaio_tests'


def db_bootstrap():
    """
    Prepares the database to run tests.

    It binds a sqlalchemy engine, recreates all db schema,
    patches `models.create_engine_from_config`, configures
    `models.Session` and `models.ScopedSession` globally
    and returns the engine.

    :returns: an instance of engine.
    """
    engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost/%s' % DB_NAME, echo=False)
    models.Base.metadata.drop_all(engine)
    models.init_database(engine)

    # patch the module function
    models.create_engine_from_config = lambda config: engine
    models.Session.configure(bind=engine)
    models.ScopedSession.configure(bind=engine)

    return engine

# Boolean constant to skip or execute tests that needs a running db.
try:
    DB_READY = bool(db_bootstrap())
except OperationalError:
    print u'''
    ##################################################################
    Testing DB is not properly configured. Many tests will be skipped.
    ##################################################################
    '''
    DB_READY = False

