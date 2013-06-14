# coding: utf-8
import sys
import os
import argparse
import subprocess
import atexit
import time


def setenv(configfile):
    abspath = os.path.abspath(configfile)
    os.environ['BALAIO_SETTINGS_FILE'] = abspath


def run_monitor(stdin=subprocess.PIPE, stdout=subprocess.PIPE):
    """
    Runs the monitor process and returns a bound subprocess.Popen
    instance.
    """
    cmd = ['python', 'monitor.py']
    monitor = subprocess.Popen(' '.join(cmd),
                               shell=True,
                               stdin=stdin,
                               stdout=stdout)

    return monitor


def run_validator(stdin=subprocess.PIPE, stdout=subprocess.PIPE):
    cmd = ['python', 'validator.py']
    validator = subprocess.Popen(' '.join(cmd),
                                 shell=True,
                                 stdin=stdin,
                                 stdout=stdout)

    return validator


def terminate(procs):
    """
    Tries to terminate all child processes on a civilized way.
    If the processes insist to live, we kill them mercilessly.
    """
    print 'Terminating child processes...'
    for p in reversed(procs):
        p.terminate()

        for t_try in range(10):
            if not p.poll():
                time.sleep(0.5)
                continue
            else:
                break
        else:
            p.kill()


def main():
    """
    Set up the processes and run indefinitely.
    """
    print 'Start listening'

    monitor = run_monitor()
    validator = run_validator(stdin=monitor.stdout)
    procs = [monitor, validator]

    # if this script is terminated by SIGTERM,
    # the terminate function will take care of
    # the child processes.
    atexit.register(terminate, procs)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=u'Balaio utility')
    parser.add_argument('-c', action='store', dest='configfile',
        required=True)

    args = parser.parse_args()
    setenv(args.configfile)

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
