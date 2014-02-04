# coding: utf-8
import sys
import os
import argparse
import logging

import utils
import models


logger = logging.getLogger('balaio.main')


def setenv(var_name, path):
    abspath = os.path.abspath(path)
    os.environ[var_name] = abspath
    logger.debug('Environment variable %s set to %s' % (var_name, abspath))


if __name__ == '__main__':
    utils.setup_logging()

    parser = argparse.ArgumentParser(description=u'Balaio utility')
    parser.add_argument('--config',
                        action='store',
                        dest='configfile',
                        required=True)
    parser.add_argument('--alembic-config',
                        action='store',
                        dest='alembic_configfile')
    parser.add_argument('activity',
                        choices=['syncdb', 'shell'])

    args = parser.parse_args()

    # setting up the required environment variables
    setenv('BALAIO_SETTINGS_FILE', args.configfile)
    if args.alembic_configfile:
        setenv('BALAIO_ALEMBIC_SETTINGS_FILE', args.alembic_configfile)

    activity = args.activity
    if activity == 'syncdb':
        # Creates all database basic structure including
        # Alembic's migration bootstrapping.

        if not args.alembic_configfile:
            sys.exit('%s: error: argument --alembic-config is required' % __file__)

        logger.info('The database infrastructure will be created')
        config = utils.balaio_config_from_env()
        engine = models.create_engine_from_config(config)
        models.init_database(engine)

        print 'Done. All databases had been created'
        sys.exit(0)

    elif activity == 'shell':
        # Places de user on an interactive shell, with a
        # pre-configured Session object.
        local_scope = {}

        def Session_factory():
            engine = models.create_engine_from_config(
                utils.balaio_config_from_env())
            models.Session.configure(bind=engine)
            return models.Session


        # Snippet from Django codebase: http://git.io/NgjYOA
        # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
        # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
        for pythonrc in (os.environ.get("PYTHONSTARTUP"), '~/.pythonrc.py'):
            if not pythonrc:
                continue
            pythonrc = os.path.expanduser(pythonrc)
            if not os.path.isfile(pythonrc):
                continue
            try:
                with open(pythonrc) as handle:
                    exec(compile(handle.read(), pythonrc, 'exec'), local_scope)
            except NameError:
                pass

        # Adding a pre-configured Session to the local scope.
        local_scope['Session'] = Session_factory()

        import code
        code.interact(local=local_scope)

