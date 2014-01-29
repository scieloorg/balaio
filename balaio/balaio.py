# coding: utf-8
import sys
import os
import argparse
import logging

import utils
import models


logger = logging.getLogger('balaio.main')


def setenv(configfile):
    abspath = os.path.abspath(configfile)
    os.environ['BALAIO_SETTINGS_FILE'] = abspath
    logger.debug('Environment variable BALAIO_SETTINGS_FILE set to %s' % abspath)


if __name__ == '__main__':
    utils.setup_logging()

    parser = argparse.ArgumentParser(description=u'Balaio utility')
    parser.add_argument('-c',
                        action='store',
                        dest='configfile',
                        required=True)
    parser.add_argument('--syncdb',
                        help='Create the basic database infrastructure and exit',
                        action='store_true')

    args = parser.parse_args()
    setenv(args.configfile)

    if args.syncdb:
        logger.info('The database infrastructure will be created')
        config = utils.balaio_config_from_env()
        engine = models.create_engine_from_config(config)
        models.init_database(engine)

        print 'Done. All databases had been created'
        sys.exit(0)

