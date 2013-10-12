# coding: utf-8
import scieloapi
import sqlalchemy

from utils import SingletonMixin, Configuration
import models


def auto_commit_or_rollback(method):
    def _method(self, *args, **kwargs):
        try:
            _return = method(self, *args, **kwargs)
            self.db_session.commit()
        except sqlalchemy.exc.IntegrityError:
            self.db_session.rollback()
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
        self.db_session = db_session
        self.checkpoint = checkpoint

        # make sure checkpoint is held by the session
        if self.checkpoint not in self.db_session:
            self.db_session.add(self.checkpoint)


    @auto_commit_or_rollback
    def tell(self, message, status, label=None):
        """
        Adds the notice on checkpoint, and sends a notification to
        SciELO Manager.

        :param message: a string
        :param status: instance of :class:`models.Status`.
        :param label: (optional)
        """
        self.checkpoint.tell(message, status, label=label)

    @auto_commit_or_rollback
    def start(self):
        self.checkpoint.start()

    @auto_commit_or_rollback
    def end(self):
        self.checkpoint.end()


class DBSessionFactory(SingletonMixin, object):
    """
    Encapsulates the `models.Session` configuration.
    """
    def __init__(self, config):
        self.config = config

    def __call__(self):
        Session = models.Session
        Session.configure(bind=models.create_engine_from_config(self.config))
        return Session


def create_checkpoint_notifier(config, point):
    SessionFactory = DBSessionFactory(config)
    Session = SessionFactory()

    scieloapi_client = None  # scieloapi.Client('some.user', 'some.key')

    def _checkin_notifier_factory(attempt):
        session = Session()
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

