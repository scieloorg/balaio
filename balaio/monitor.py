#coding: utf-8
import sys

import pyinotify

from utils import Configuration


config = Configuration.from_env()

mask = pyinotify.IN_CLOSE_WRITE


class EventHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        # CALL CHECKIN
        sys.stdout.write("WRITE AND CLOSE: %s\n" % event.pathname)
        sys.stdout.flush()


if __name__ == '__main__':

    wm = pyinotify.WatchManager()
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)

    wm.add_watch(config.get('monitor', 'watch_path').split(','),
                 mask,
                 rec=config.get('monitor', 'recursive'),
                 auto_add=config.get('monitor', 'recursive'))

    notifier.loop(pid_file=config.get('monitor', 'pid_file'))
