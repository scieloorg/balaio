#coding: utf-8
import os
import threading
import Queue
import logging
import sys
import zipfile

import pyinotify
import transaction

import utils
import checkin
import models
import excepts
import notifier


logger = logging.getLogger('balaio.monitor')

#IN_CREATE event must be set to watch new directories
#https://github.com/seb-m/pyinotify/wiki/Frequently-Asked-Questions
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE


class Monitor(object):
    def __init__(self, workers=None):
        self.job_queue = Queue.Queue()
        self.total_workers = workers if workers else 1

        self.config = utils.Configuration.from_env()
        self.CheckinNotifier = notifier.checkin_notifier_factory(self.config)
        self.Session = models.Session
        self.Session.configure(bind=models.create_engine_from_config(self.config))


        self.running_workers = []
        for w in range(self.total_workers):
            thread = threading.Thread(target=self.handle_events, args=(self.job_queue,))
            self.running_workers.append(thread)
            thread.start()

    def handle_events(self, job_queue):
        while True:
            filepath = job_queue.get()
            logger.debug('Started handling event for %s' % filepath)

            try:
                attempt = checkin.get_attempt(filepath)

            except ValueError as e:
                try:
                    utils.mark_as_failed(filepath)
                except OSError as e:
                    logger.debug('The file is gone before marked as failed. %s' % e)

                logger.debug('Failed during checkin: %s: %s' % (filepath, e))

            except excepts.DuplicatedPackage as e:
                try:
                    utils.mark_as_duplicated(filepath)
                except OSError as e:
                    logger.debug('The file is gone before marked as duplicated. %s' % e)

            else:
                utils.send_message(sys.stdout, attempt, utils.make_digest)
                logging.debug('Message sent for %s: %s, %s' % (filepath,
                    repr(attempt), repr(utils.make_digest)))

                # Create a notification to keep track of the checkin process
                session = self.Session()
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

    def trigger_event(self, filepath):
        self.job_queue.put(filepath)


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)
        self.monitor = Monitor()

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
    config = utils.Configuration.from_env()
    utils.setup_logging()

    wm = pyinotify.WatchManager()
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(config.get('monitor', 'watch_path').split(','),
                 mask,
                 rec=config.get('monitor', 'recursive'),
                 auto_add=config.get('monitor', 'recursive'))

    logger.info('Watching %s' % config.get('monitor', 'watch_path'))

    notifier.loop()

