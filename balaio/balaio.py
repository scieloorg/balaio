# coding: utf-8
import argparse
import subprocess
try:
    import cPickle as pickle
except ImportError:
    import pickle

import utils


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
        type=argparse.FileType('rt'), required=True)

    args = parser.parse_args()

    config = utils.Configuration(args.configfile)

    monitor = run_monitor()
