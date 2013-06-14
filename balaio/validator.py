# coding: utf-8
import sys

import plumber

import utils
from models import Attempt


class ExamplePipe(plumber.Pipe):
    def transform(data):
        return data


ppl = plumber.Pipeline(ExamplePipe)

if __name__ == '__main__':
    messages = utils.recv_messages(sys.stdin, utils.make_digest)
    try:
        results = [msg for msg in ppl.run(messages)]
    except KeyboardInterrupt:
        sys.exit(0)
