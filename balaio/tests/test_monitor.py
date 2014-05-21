import unittest

import mocker
from sqlalchemy.exc import OperationalError

from balaio import monitor
from balaio.lib import models
from balaio.lib import excepts
from . import doubles
from .utils import db_bootstrap, DB_READY

global_engine = None


def setUpModule():
    """
    Initialize the database.
    """
    global global_engine
    try:
        global_engine = db_bootstrap()
    except OperationalError:
        # global_engine remains None, all db-bound testcases
        # need to test for DB_READY before run.
        pass


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


class ProcessPackageFunctionTests(mocker.MockerTestCase):

    def tearDown(self):
        models.ScopedSession.remove()

    @unittest.skipUnless(DB_READY, u'DB must be set. Make sure `app_balaio_tests` is properly configured.')
    def test_invalid_package(self):
        safepack = doubles.SafePackageFake('fixtures/invalid_rsp-v47n4.zip', '/tmp')

        checkin_mod = self.mocker.replace('balaio.lib.checkin')
        checkin_mod.get_attempt(mocker.ANY)
        self.mocker.throw(excepts.InvalidXML)

        patched_safepack = self.mocker.patch(safepack)
        patched_safepack.mark_as_failed(silence=True)
        self.mocker.result(None)
        self.mocker.replay()

        self.assertIsNone(monitor.process_package(patched_safepack, None))

