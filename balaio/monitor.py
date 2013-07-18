#coding: utf-8
import logging
import sys

import checkin
import zipfile
import pyinotify

import utils


logger = logging.getLogger('balaio.monitor')
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE


class EventHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        filepath = event.pathname

        logger.info('Package detected: %s' % filepath)

        if not zipfile.is_zipfile(filepath):
            logger.info('Invalid zipfile: %s' % filepath)
            return None

        try:
            attempt = checkin.get_attempt(filepath)
        except ValueError:
            utils.mark_as_failed(filepath)
            logger.info('Failed during checkin: %s' % filepath)
        else:
            utils.send_message(sys.stdout, attempt, utils.make_digest)
            logging.debug('Message sent for %s: %s, %s' % (filepath,
                repr(attempt), repr(utils.make_digest)))


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

