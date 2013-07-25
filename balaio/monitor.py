#coding: utf-8
import threading
import Queue
import logging
import sys

import checkin
import zipfile
import pyinotify

import utils


logger = logging.getLogger('balaio.monitor')
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_TO


class Monitor(object):
    def __init__(self, workers=None):
        self.job_queue = Queue.Queue()
        self.total_workers = workers if workers else 1

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
            else:
                utils.send_message(sys.stdout, attempt, utils.make_digest)
                logging.debug('Message sent for %s: %s, %s' % (filepath,
                    repr(attempt), repr(utils.make_digest)))

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
        filepath = event.pathname
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

