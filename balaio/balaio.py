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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=u'Balaio utility')
    parser.add_argument('-c', action='store', dest='configfile',
                        required=True)

    args = parser.parse_args()
    setenv(args.configfile)

    monitor = run_monitor()
    validator = run_validator(stdin=monitor.stdout)

    print 'Start listening'
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    finally:
        print 'Terminating all child processess'
        validator.terminate()
        monitor.terminate()
