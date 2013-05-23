#
# Monitor Module
#

import sys
import ConfigParser
import pyinotify

config = ConfigParser.RawConfigParser()
config.read('../config.ini')

mask = pyinotify.IN_CLOSE_WRITE


class EventHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        # CALL CHECKIN
        print "WRITE AND CLOSE:", event.pathname

wm = pyinotify.WatchManager()
handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)

wm.add_watch(config.get('paths', 'watch_path').split(','), mask,
             rec=config.get('params', 'recursive'),
             auto_add=config.get('params', 'auto_add'))

try:
    notifier.loop(daemonize=config.get('params', 'daemonize'),
                  pid_file=config.get('paths', 'pid_file'),
                  stdout=config.get('paths', 'output'))
except pyinotify.NotifierError, err:
    print >> sys.stderr, err
