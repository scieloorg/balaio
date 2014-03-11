#coding: utf-8
import os
import datetime
import ConfigParser

from sqlalchemy.exc import OperationalError


class CheckItem(object):
    """
    Represents an item that needs to be checked.
    """
    def __call__(self):
        """
        Performs the check step for a specific app aspect.
        """
        raise NotImplementedError()

    def structured(self):
        return {'description': self.__class__.__doc__.strip(),
                'status': self()}


class CheckList(object):
    """
    Performs a sequence of checks related to the application health.
    """
    def __init__(self, refresh=1):
        """
        :param refresh: (optional) refresh rate in minutes.
        """
        self.latest_report = {}

        self._check_list = []
        self._refresh_rate = datetime.timedelta(minutes=refresh)
        self._refreshed_at = None

    def add_check(self, check):
        """
        Add a check to the registry.

        :param check: a callable that receives nothing as argument.
        """
        assert isinstance(check, CheckItem)
        self._check_list.append(check)

    def run(self):
        """
        Run all checks sequentially and updates the object state.
        """
        self.latest_report = {check: check.structured() for check in self._check_list}
        self._refreshed_at = datetime.datetime.now()

    def update(self):
        """
        Run all checks respecting the refresh rate.
        """
        if self._refreshed_at is None or (
            self._refreshed_at + self._refresh_rate <= datetime.datetime.now()):

            self.run()

    def since(self):
        """
        Total seconds since the last refresh.
        """
        return str(datetime.datetime.now() - self._refreshed_at)


class DBConnection(CheckItem):
    """
    The DB connection must be active and operating.
    """

    def __init__(self, engine):
        self.engine = engine

    def __call__(self):
        """
        Try to list table names just to reach the db.
        """
        try:
            _ = self.engine.table_names()
        except OperationalError:
            return False
        else:
            return True


class Monitor(CheckItem):
    """
    The Monitor process must be active in Circus.
    """

    def __call__(self):
        """
        Try to check if the monitor process is active.
        """
        status = os.popen('circusctl status monitor').read().strip()

        if status == 'active':
            return True

        return False


class Validator(CheckItem):
    """
    The Validator process must be active in Circus.
    """

    def __call__(self):
        """
        Try to check if the validator process is active.
        """
        status = os.popen('circusctl status validator').read().strip()

        if status == 'active':
            return True

        return False


class NotificationsOption(CheckItem):
    """
    All generated notifications must be sent to SciELO Manager.
    """
    def __init__(self, config):
        self.config = config

    def __call__(self):
        try:
            return self.config.getboolean('manager', 'notifications')
        except ConfigParser.Error:
            return False
