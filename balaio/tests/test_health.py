import unittest

import mocker
import os

from balaio import health


class CheckItem(unittest.TestCase):
    def test_call_must_be_implemented(self):
        class CheckIt(health.CheckItem):
            pass

        check = CheckIt()
        self.assertRaises(NotImplementedError, check)


class MonitorTests(mocker.MockerTestCase):

    def test_monitor_is_health(self):
        mock_os = self.mocker.replace(os)
        mock_os.popen('circusctl status monitor').read()
        self.mocker.result('active\n')
        self.mocker.replay()

        monitor = health.Monitor()
        self.assertTrue(monitor())

    def test_monitor_is_dead(self):
        mock_os = self.mocker.replace(os)
        mock_os.popen('circusctl status monitor').read()
        self.mocker.result('stopped\n')
        self.mocker.replay()

        monitor = health.Monitor()
        self.assertFalse(monitor())


class ValidatorTests(mocker.MockerTestCase):

    def test_validator_is_health(self):
        mock_os = self.mocker.replace(os)
        mock_os.popen('circusctl status validator').read()
        self.mocker.result('active\n')
        self.mocker.replay()

        validator = health.Validator()
        self.assertTrue(validator())

    def test_validator_is_dead(self):
        mock_os = self.mocker.replace(os)
        mock_os.popen('circusctl status validator').read()
        self.mocker.result('stopped\n')
        self.mocker.replay()

        validator = health.Validator()
        self.assertFalse(validator())


class DBConnectionTests(mocker.MockerTestCase):

    def test_tablenames_are_queried(self):
        mock_engine = self.mocker.mock()
        mock_engine.table_names()
        self.mocker.result(['foo'])
        self.mocker.replay()

        dbconn = health.DBConnection(mock_engine)
        self.assertTrue(dbconn())

    def test_exceptions_return_false(self):
        from sqlalchemy.exc import OperationalError

        mock_engine = self.mocker.mock()
        mock_engine.table_names()
        self.mocker.throw(OperationalError('foo', None, None))
        self.mocker.replay()

        dbconn = health.DBConnection(mock_engine)
        self.assertFalse(dbconn())

    def test_structured(self):
        """
        Gets the docstring as the description and the status.
        """
        dbconn = health.DBConnection(None)

        mock_dbconn = self.mocker.patch(dbconn)
        mock_dbconn()
        self.mocker.result(True)
        self.mocker.replay()

        self.assertEqual(dbconn.structured(),
            {'description': 'The DB connection must be active and operating.',
             'status': True})


class CheckListTests(mocker.MockerTestCase):

    def test_refresh_in_minutes(self):
        import datetime
        check_list = health.CheckList(refresh=2)
        self.assertEqual(datetime.timedelta(minutes=2),
            check_list._refresh_rate)

    def test_latest_refresh_date_starts_as_None(self):
        check_list = health.CheckList(refresh=2)
        self.assertIsNone(check_list._refreshed_at)


    def test_add_check(self):
        check_list = health.CheckList(refresh=2)
        self.assertEqual(len(check_list._check_list), 0)

        class CheckIt(health.CheckItem):
            def __call__(self):
                return True

        check_list.add_check(CheckIt())
        self.assertEqual(len(check_list._check_list), 1)

    def test_run(self):

        class CheckIt(health.CheckItem):
            """There be dragons"""
            def __call__(self):
                return True

        check_list = health.CheckList(refresh=2)
        check = CheckIt()
        check_list.add_check(check)
        check_list.run()

        self.assertEqual(check_list.latest_report,
            {check: {'status': True, 'description': 'There be dragons'}})

    def test_since(self):
        """
        The elapsed time since the last refresh.
        """
        import datetime
        dt1 = datetime.datetime(2013, 12, 15, 10, 10, 10)
        dt2 = datetime.datetime(2013, 12, 15, 10, 11, 10)

        check_list = health.CheckList(refresh=1)
        check_list._refreshed_at = dt1

        mock_datetime = self.mocker.replace(datetime)
        mock_datetime.datetime.now()
        self.mocker.result(dt2)
        self.mocker.replay()

        self.assertEqual(check_list.since(), '0:01:00')


class NotificationsTests(mocker.MockerTestCase):

    def test_notifications_is_on(self):
        mock_config = self.mocker.mock()
        mock_config.getboolean('manager', 'notifications')
        self.mocker.result(True)
        self.mocker.replay()

        notifications = health.NotificationsOption(mock_config)
        self.assertTrue(notifications())

    def test_structured_description(self):
        mock_config = self.mocker.mock()
        mock_config.getboolean('manager', 'notifications')
        self.mocker.result(True)
        self.mocker.replay()

        notifications = health.NotificationsOption(mock_config)
        self.assertTrue(notifications.structured(),
            {'description': 'All generated notifications must be sent to SciELO Manager.',
             'status': True})

    def test_notifications_opt_is_missing(self):
        import ConfigParser

        mock_config = self.mocker.mock()
        mock_config.getboolean('manager', 'notifications')
        self.mocker.throw(ConfigParser.NoOptionError('manager', 'notifications'))
        self.mocker.replay()

        notifications = health.NotificationsOption(mock_config)
        self.assertFalse(notifications())
