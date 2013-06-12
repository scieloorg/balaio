#coding: utf-8
import sys

import checkin
import pyinotify

import utils


config = utils.Configuration.from_env()

mask = pyinotify.IN_CLOSE_WRITE


class EventHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        filepath = event.pathname
        try:
            attempt = checkin.get_attempt(filepath)
        except ValueError:
            utils.mark_as_failed(filepath)
        else:
            utils.send_message(sys.stdout, attempt, utils.make_digest)


if __name__ == '__main__':
    wm = pyinotify.WatchManager()
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(config.get('monitor', 'watch_path').split(','),
                 mask,
                 rec=config.get('monitor', 'recursive'),
                 auto_add=config.get('monitor', 'recursive'))

    notifier.loop(pid_file=config.get('monitor', 'pid_file'))

