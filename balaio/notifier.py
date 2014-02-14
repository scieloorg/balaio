# coding: utf-8
import logging

import scieloapi
import sqlalchemy
import transaction

import models


logger = logging.getLogger(__name__)


def auto_commit_or_rollback(method):
    """
    Performs a commit if changes are made to the session or abort on errors.
    """
    def _method(self, *args, **kwargs):
        try:
            _return = method(self, *args, **kwargs)
            if self.db_session.dirty:
                transaction.commit()
        except sqlalchemy.exc.IntegrityError:
            transaction.abort()
            raise
        else:
            return _return

    return _method


class Notifier(object):
    """
    Acts as a broker to notifications.
    """

    def __init__(self, checkpoint, scieloapi_client,
                 db_session, manager_integration=True):
        """
        :param checkpoint: is a :class:`models.Checkpoint` instance.
        :param scieloapi_client: instance of `scieloapi.Client`.
        :param db_session: sqlalchemy session.
        :param manager_integration: (optional) if notifications must be sent to manager.
        """
        self.scieloapi = scieloapi_client
        self.checkpoint = checkpoint
        self.db_session = db_session
        self.manager_integration = manager_integration

        # make sure checkpoint is held by the session
        if self.checkpoint not in self.db_session:
            self.db_session.add(self.checkpoint)

    def tell(self, message, status, label=None):
        """
        Adds the notice on checkpoint, and sends a notification to
        SciELO Manager.

        :param message: a string
        :param status: instance of :class:`models.Status`.
        :param label: (optional)
        """
        self.checkpoint.tell(message, status, label=label)
        self._send_notice_notification(message, status, label=label)

    def start(self):
        self.checkpoint.start()
        if self.checkpoint.point is models.Point.checkin:
            self._send_checkin_notification()

    def end(self):
        self.checkpoint.end()
        if self.checkpoint.point is models.Point.checkout:
            self._send_checkout_notification()

    def _send_checkout_notification(self):
        """
        Sends a checkout notification to SciELO Manager.

        Only checkpoints of type checkout can send call this method
        """
        if not self.manager_integration:
            logger.warning('Notifications to Manager are disabled. Skipping.')
            return None

        assert self.checkpoint.point is models.Point.checkout, 'only `checkout` checkpoint can send this notification.'

        data = {
            'checkin': self.checkpoint.attempt.checkin_uri,
            'stage': 'checkout',
            'checkpoint': self.checkpoint.point.name,
            'message': 'checkout finished',
            'status': 'ok',
        }

        try:
            self.scieloapi.notices.post(data)
        except scieloapi.exceptions.APIError as e:
            logger.error('Error posting data to Manager. Message: %s' % e)

    def _send_checkin_notification(self):
        """
        Sends a checkin notification to SciELO Manager.

        Only checkpoints of type checkin can send call this method.
        As a side effect of creating a new checkin on SciELO Manager,
        the attribute `self._checkin_resource_uri` is bound to its
        resource uri.
        """
        if not self.manager_integration:
            logger.warning('Notifications to Manager are disabled. Skipping.')
            return None

        assert self.checkpoint.point is models.Point.checkin, 'only `checkin` checkpoint can send this notification.'

        data = {
                 'articlepkg_ref': str(self.checkpoint.attempt.articlepkg.id),
                 'attempt_ref': str(self.checkpoint.attempt.id),
                 'article_title': self.checkpoint.attempt.articlepkg.article_title,
                 'journal_title': self.checkpoint.attempt.articlepkg.journal_title,
                 'issue_label': self.checkpoint.attempt.articlepkg.issue_label,
                 'package_name': self.checkpoint.attempt.filepath,
                 'pissn': self.checkpoint.attempt.articlepkg.journal_pissn,
                 'eissn': self.checkpoint.attempt.articlepkg.journal_eissn,
                 'uploaded_at': str(self.checkpoint.attempt.started_at),
               }
        resource_uri = '/api/v1/checkins/%s/'

        try:
            resource_id = self.scieloapi.checkins.post(data)
        except scieloapi.exceptions.APIError as e:
            logger.error('Error posting data to Manager. Message: %s' % e)
        else:
            self.checkpoint.attempt.checkin_uri = resource_uri % resource_id

    def _send_notice_notification(self, message, status, label=None):
        """
        Sends notices notifications bound to the active checkin, to SciELO Manager.
        """
        if not self.manager_integration:
            logger.warning('Notifications to Manager are disabled. Skipping.')
            return None

        data = {
            'checkin': self.checkpoint.attempt.checkin_uri,
            'stage': label,
            'checkpoint': self.checkpoint.point.name,
            'message': message,
            'status': status.name,
        }

        try:
            self.scieloapi.notices.post(data)
        except scieloapi.exceptions.APIError as e:
            logger.error('Error posting data to Manager. Message: %s' % e)


def create_checkpoint_notifier(config, point):
    scieloapi_client = scieloapi.Client(config.get('manager', 'api_username'),
                                        config.get('manager', 'api_key'),
                                        api_uri=config.get('manager', 'api_url'))

    def _checkin_notifier_factory(attempt, session):
        try:
            checkpoint = session.query(models.Checkpoint).filter(
                models.Checkpoint.attempt == attempt).filter(
                models.Checkpoint.point == point.value).one()
        except sqlalchemy.orm.exc.NoResultFound:
            checkpoint = models.Checkpoint(point)
            checkpoint.attempt = attempt
        except sqlalchemy.orm.exc.MultipleResultsFound as e:
            #logger.error(e.message)
            pass

        return Notifier(checkpoint,
                        scieloapi_client,
                        session,
                        manager_integration=config.getboolean('manager', 'notifications'))

    return _checkin_notifier_factory


def checkin_notifier_factory(config):
    """
    Creates a :class:`Notifier` bound to a :attribute:`models.Checkpoint.checkin`

    Usage::

        >>> first_attempt = models.Attempt()
        >>> CheckinNotifier = checkin_notifier_factory(config)
        >>> first_attempt_notifier = CheckinNotifier(first_attempt)
        >>> first_attempt_notifier.start()
    """
    return create_checkpoint_notifier(config, models.Point.checkin)


def validation_notifier_factory(config):
    """
    Creates a :class:`Notifier` bound to a :attribute:`models.Checkpoint.validation`

    Usage::

        >>> first_attempt = models.Attempt()
        >>> ValidationNotifier = validation_notifier_factory(config)
        >>> first_attempt_notifier = ValidationNotifier(first_attempt)
        >>> first_attempt_notifier.start()
    """
    return create_checkpoint_notifier(config, models.Point.validation)


def checkout_notifier_factory(config):
    """
    Creates a :class:`Notifier` bound to a :attribute:`models.Checkpoint.checkout`

    Usage::

        >>> first_attempt = models.Attempt()
        >>> CheckoutNotifier = checkout_notifier_factory(config)
        >>> first_attempt_notifier = CheckoutNotifier(first_attempt)
        >>> first_attempt_notifier.start()
    """
    return create_checkpoint_notifier(config, models.Point.checkout)

