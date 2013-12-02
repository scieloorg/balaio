from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from balaio import models


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
    engine = create_engine('postgresql+psycopg2://postgres:123@localhost:5432/%s' % DB_NAME, echo=False)
    try:
        models.Base.metadata.drop_all(engine)
    except OperationalError as e:
        exit('You DB is not properly configured. Make sure the db `%s` exists. Traceback: %s' % (DB_NAME, e))
    models.init_database(engine)

    # patch the module function
    models.create_engine_from_config = lambda config: engine
    models.Session.configure(bind=engine)
    models.ScopedSession.configure(bind=engine)

    return engine

