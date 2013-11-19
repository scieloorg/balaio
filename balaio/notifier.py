# coding: utf-8
import scieloapi
import sqlalchemy
import transaction

import models


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

    def __init__(self, checkpoint, scieloapi_client, db_session):
        """
        :param checkpoint: is a :class:`models.Checkpoint` instance.
        :param scieloapi_client: instance of `scieloapi.Client`.
        :param db_session:
        """
        self.scieloapi = scieloapi_client
        self.checkpoint = checkpoint
        self.db_session = db_session

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

    def start(self):
        self.checkpoint.start()
        if self.checkpoint.point is models.Point.checkin:
            self._send_checkin_notification()

    def end(self):
        self.checkpoint.end()

    def _send_checkin_notification(self):
        """
        Sends a checkin notification to SciELO Manager.
        Only checkpoints of type checkin can send call this method.
        """
        assert self.checkpoint.point is models.Point.checkin, 'only `checkin` checkpoint can send this notification.'

        data = {
                 'articlepkg_ref': self.checkpoint.attempt.articlepkg.id,
                 'attempt_ref': self.checkpoint.attempt.id,
                 'article_title': self.checkpoint.attempt.articlepkg.article_title,
                 'journal_title': self.checkpoint.attempt.articlepkg.journal_title,
                 'issue_label': '##',
                 'package_name': self.checkpoint.attempt.filepath,
                 'uploaded_at': self.checkpoint.attempt.started_at,
               }
        self.scieloapi.checkins.post(data)


def create_checkpoint_notifier(config, point):
    scieloapi_client = scieloapi.Client(config.get('manager', 'api_username'),
                                        config.get('manager', 'api_key'))

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
                        session)

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

