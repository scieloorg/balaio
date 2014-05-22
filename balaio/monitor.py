#coding: utf-8
import os
import threading
import Queue
import logging
import zipfile

import pyinotify
import transaction

from lib import (
    utils,
    checkin,
    models,
    excepts,
    notifier,
    package,
)


logger = logging.getLogger('balaio.monitor')

#IN_CREATE event must be set to watch new directories
#https://github.com/seb-m/pyinotify/wiki/Frequently-Asked-Questions
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE


def process_package(pack, notifier):
    """Perform the checkin process for one package.

    This method does not return any value.
    :param pack: `lib.package.SafePackage` instance.
    :param notifier: `lib.notifier.Notifier` instance.
    """
    logger.debug('Started processing %s.' % pack)

    pack_reporter = package.CheckinReporter(pack.primary_path)
    pack_reporter.tell('Started the identification process.')

    try:
        attempt = checkin.get_attempt(pack)

    except excepts.MissingXML as e:
        pack.mark_as_failed(silence=True)
        pack_reporter.tell('The package must have only one XML file.')

    except excepts.InvalidXML as e:
        pack.mark_as_failed(silence=True)
        for msg in e.message:
            pack_reporter.tell(msg)

    except excepts.DuplicatedPackage as e:
        pack.mark_as_failed(silence=True)
        pack_reporter.tell('The package was already deposited.')

    except Exception as e:
        pack.mark_as_failed(silence=True)
        pack_reporter.tell('The package could not be processed due to an unexpected error. Our engineers have been notified.')

    else:
        # Create a notification to keep track of the checkin process
        session = models.Session()
        checkin_notifier = notifier(attempt, session)
        checkin_notifier.start()

        if attempt.is_valid:
            notification_msg = 'Attempt ready to be validated'
            notification_status = models.Status.ok
        else:
            notification_msg = 'Attempt cannot be validated'
            notification_status = models.Status.error

        pack_reporter.tell('The package is ready to be validated.')
        checkin_notifier.tell('XML validates against the SPS Schema',
            notification_status, 'Checkin')
        checkin_notifier.tell(notification_msg, notification_status, 'Checkin')
        checkin_notifier.end()

        attempt.proceed_to_validation = True
        transaction.commit()


class WorkerPool(object):
    """Pool of checkin processors.

    The pool is initialized during the instance initialization,
    and after being shutdown, it is not possible to restart it. Sorry =]
    """
    shutdown_sentinel = '##HALT##'

    def __init__(self, config, size=None):
        self.job_queue = Queue.Queue()
        self.total_workers = size or 1
        self.config = config
        self.running_workers = None

        self.CheckinNotifier = notifier.checkin_notifier_factory(self.config)
        self._setup_workers()

    def __del__(self):
        self.shutdown()

    def _setup_workers(self):
        self.running_workers = []
        for w in range(self.total_workers):
            thread = threading.Thread(target=self._handle_events, args=(self.job_queue,))
            self.running_workers.append(thread)
            thread.start()

    def _handle_events(self, job_queue):
        while True:
            filepath = job_queue.get()
            if filepath == self.shutdown_sentinel:
                return None

            pack = package.SafePackage(filepath, self.config.get('app', 'working_dir'))
            process_package(pack, self.CheckinNotifier)

    def add_job(self, filepath):
        """Add a new package to be processed by the pool.

        :param filepath: is a string of the absolute path to the package file.
        """
        self.job_queue.put(filepath)

    def shutdown(self):
        """Send a shutdown signal to all running workers.

        All running workers are terminated gracefully.
        """
        for _ in range(len(self.running_workers)):
            self.add_job(self.shutdown_sentinel)


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, *args, **kwargs):
        config = kwargs.pop('config', None)
        super(EventHandler, self).__init__(*args, **kwargs)

        if not config:
            raise TypeError(u'__init__() expects a config kwarg')

        self.pool = WorkerPool(config)

    def process_IN_CLOSE_WRITE(self, event):
        logger.debug('IN_CLOSE_WRITE event handler for %s.' % event)
        self._do_the_job(event)

    def process_IN_MOVE_SELF(self, event):
        logger.debug('IN_MOVE_SELF event handler for %s.' % event)
        self._do_the_job(event)

    def process_IN_MOVED_TO(self, event):
        logger.debug('IN_MOVED_TO event handler for %s.' % event)
        self._do_the_job(event)

    def _do_the_job(self, event):
        """
        Add the package in a processing queue.

        All filenames prefixed with `_` are identified as special packages
        and are ignored by the system.
        """
        filepath = event.pathname
        if not os.path.basename(filepath).startswith('_'):
            if not zipfile.is_zipfile(filepath):
                logger.info('Invalid zipfile: %s.' % filepath)
                return None

            logger.debug('Adding %s to checkin processing pool.' % filepath)
            self.pool.add_job(filepath)


if __name__ == '__main__':
    # App bootstrapping:
    # Setting up the app configuration, logging and SqlAlchemy Session.
    config = utils.balaio_config_from_env()
    utils.setup_logging(config)
    models.Session.configure(bind=models.create_engine_from_config(config))

    # Setting up PyInotify event watcher.
    wm = pyinotify.WatchManager()
    handler = EventHandler(config=config)
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(config.get('monitor', 'watch_path').split(','),
                 mask,
                 rec=config.getboolean('monitor', 'recursive'),
                 auto_add=config.getboolean('monitor', 'recursive'))

    logger.info('Watching %s.' % config.get('monitor', 'watch_path'))

    notifier.loop()

