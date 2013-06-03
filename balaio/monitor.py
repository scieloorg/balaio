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

wm = pyinotify.WatchManager()
handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

wm.add_watch(config.get('paths', 'watch_path').split(','),
             mask,
             rec=config.get('params', 'recursive'),
             auto_add=config.get('params', 'recursive'))

notifier.loop(pid_file=config.get('paths', 'pid_file'))
