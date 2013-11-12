from sqlalchemy import create_engine

from balaio import models


def db_bootstrap():
    """
    Prepares the database to run tests.

    It binds a sqlalchemy engine, creates all db schema,
    patches `models.create_engine_from_config`, configures
    `models.Session` and `models.ScopedSession` globally
    and returns the engine.

    :returns: an instance of engine.
    """
    engine = create_engine('postgresql+psycopg2://postgres:@localhost/app_balaio', echo=False)
    models.init_database(engine)

    # patch the module function
    models.create_engine_from_config = lambda config: engine
    models.Session.configure(bind=engine)
    models.ScopedSession.configure(bind=engine)

    return engine

