#coding: utf-8
import os
import time
import threading
import Queue
import logging
import zipfile
import socket

import pyinotify
import transaction

import utils
import checkin
import models
import excepts
import notifier
import package


logger = logging.getLogger('balaio.monitor')

#IN_CREATE event must be set to watch new directories
#https://github.com/seb-m/pyinotify/wiki/Frequently-Asked-Questions
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE


class Monitor(object):
    def __init__(self, config, workers=None):
        self.job_queue = Queue.Queue()
        self.total_workers = workers or 1
        self.config = config

        self.CheckinNotifier = notifier.checkin_notifier_factory(self.config)
        self._setup_sock()
        self._setup_workers()

    def _setup_sock(self):
        while True:
            try:
                self.stream = utils.get_writable_socket(self.config.get('app', 'socket'))
                break
            except socket.error:
                logger.info('Trying to estabilish connection with module `validator`. Please wait...')
                time.sleep(0.5)
            else:
                logger.info('Connection estabilished with `validator`.')

    def _setup_workers(self):
        self.running_workers = []
        for w in range(self.total_workers):
            thread = threading.Thread(target=self.handle_events, args=(self.job_queue,))
            self.running_workers.append(thread)
            thread.start()

    def handle_events(self, job_queue):
        while True:
            filepath = job_queue.get()
            logger.debug('Started handling event for %s' % filepath)

            pack = package.SafePackage(filepath, self.config.get('app', 'working_dir'))
            try:
                attempt = checkin.get_attempt(pack)

            except ValueError as e:
                pack.mark_as_failed(silence=True)

            except excepts.DuplicatedPackage as e:
                pack.mark_as_duplicated(silence=True)

            else:
                # Create a notification to keep track of the checkin process
                session = models.Session()
                checkin_notifier = self.CheckinNotifier(attempt, session)
                checkin_notifier.start()

                if attempt.is_valid:
                    notification_msg = 'Attempt ready to be validated'
                    notification_status = models.Status.ok
                else:
                    notification_msg = 'Attempt cannot be validated'
                    notification_status = models.Status.error

                checkin_notifier.tell(notification_msg, notification_status, 'Checkin')
                checkin_notifier.end()

                transaction.commit()

                #Send stream
                utils.send_message(self.stream, attempt, utils.make_digest)
                logging.debug('Message sent for %s: %s, %s' % (filepath,
                    repr(attempt), repr(utils.make_digest)))

    def trigger_event(self, filepath):
        self.job_queue.put(filepath)


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, *args, **kwargs):
        config = kwargs.pop('config', None)
        super(EventHandler, self).__init__(*args, **kwargs)

        if not config:
            raise TypeError(u'__init__() expects a config kwarg')

        self.monitor = Monitor(config)

    def process_IN_CLOSE_WRITE(self, event):
        logger.debug('IN_CLOSE_WRITE event handler for %s' % event)
        self._do_the_job(event)

    def process_IN_MOVE_SELF(self, event):
        logger.debug('IN_MOVE_SELF event handler for %s' % event)
        self._do_the_job(event)

    def process_IN_MOVED_TO(self, event):
        logger.debug('IN_MOVED_TO event handler for %s' % event)
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
                logger.info('Invalid zipfile: %s' % filepath)
                return None

            self.monitor.trigger_event(filepath)


if __name__ == '__main__':
    # App bootstrapping:
    # Setting up the app configuration, logging and SqlAlchemy Session.
    config = utils.balaio_config_from_env()
    utils.setup_logging()
    models.Session.configure(bind=models.create_engine_from_config(config))

    # Setting up PyInotify event watcher.
    wm = pyinotify.WatchManager()
    handler = EventHandler(config=config)
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(config.get('monitor', 'watch_path').split(','),
                 mask,
                 rec=config.getboolean('monitor', 'recursive'),
                 auto_add=config.getboolean('monitor', 'recursive'))

    logger.info('Watching %s' % config.get('monitor', 'watch_path'))

    notifier.loop()

