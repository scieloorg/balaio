import unittest

from balaio import monitor
from . import doubles


class WorkerPoolTests(unittest.TestCase):

    def test_pool_size(self):
        config = doubles.ConfigurationStub()
        wpool = monitor.WorkerPool(config, size=1)

        self.assertEqual(len(wpool.running_workers), 1)

    def test_shutting_down_workers(self):
        config = doubles.ConfigurationStub()
        wpool = monitor.WorkerPool(config, size=2)

        for worker in wpool.running_workers:
            self.assertTrue(worker.is_alive())

        wpool.shutdown()
        import time; time.sleep(0.2)  # calm down...
        for worker in wpool.running_workers:
            self.assertFalse(worker.is_alive())


