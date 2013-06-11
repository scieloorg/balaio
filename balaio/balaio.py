# coding: utf-8
import os
import argparse
import subprocess


def setenv(configfile):
    abspath = os.path.abspath(configfile)
    os.environ['BALAIO_SETTINGS_FILE'] = abspath


def run_monitor(stdin=subprocess.PIPE, stdout=subprocess.PIPE):
    """
    Runs the monitor process and returns a bound subprocess.Popen
    instance.
    """
    cmd = ['python', 'monitor.py']
    monitor = subprocess.Popen(' '.join(cmd), shell=True, stdin=stdin,
        stdout=stdout)

    return monitor


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=u'Balaio utility')
    parser.add_argument('-c', action='store', dest='configfile',
        required=True)

    args = parser.parse_args()
    setenv(args.configfile)

    monitor = run_monitor()

    print 'Start listening'
    try:
        while True:
            out = monitor.stdout.readline()
            print 'OUT: %r' % out
    except KeyboardInterrupt:
        pass
    finally:
        print 'Terminating all child processess'
        monitor.terminate()
