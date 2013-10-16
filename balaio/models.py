#coding: utf-8
import datetime
import logging

import enum

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    ForeignKey,
    DateTime,
    String,
    Boolean,
    Table,
)
from sqlalchemy.orm import (
    relationship,
    backref,
    scoped_session,
    sessionmaker,
)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from zope.sqlalchemy import ZopeTransactionExtension


logger = logging.getLogger(__name__)

#Use scoped_session only to web app
ScopedSession = scoped_session(
    sessionmaker(expire_on_commit=False, extension=ZopeTransactionExtension()))

Session = sessionmaker(expire_on_commit=False, extension=ZopeTransactionExtension())
Base = declarative_base()


def create_engine_from_config(config):
    """
    Create a sqlalchemy.engine using values from utils.Configuration.
    """
    return create_engine(config.get('app', 'db_dsn'),
                         echo=config.getboolean('app', 'debug'))


def init_database(engine):
    """
    Creates the database structure for the application.
    """
    Base.metadata.create_all(engine)


class Attempt(Base):
    __tablename__ = 'attempt'

    id = Column(Integer, primary_key=True)
    package_checksum = Column(String(length=32), unique=True)
    articlepkg_id = Column(Integer, ForeignKey('articlepkg.id'), nullable=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    collection_uri = Column(String)
    filepath = Column(String)
    is_valid = Column(Boolean)

    articlepkg = relationship('ArticlePkg',
                              backref=backref('attempts',
                              cascade='all, delete-orphan'))

    def __init__(self, *args, **kwargs):
        super(Attempt, self).__init__(*args, **kwargs)
        self.started_at = datetime.datetime.now()
        self.is_valid = kwargs.get('is_valid', True)

    def to_dict(self):

        checkpoints = {cp.point.name: cp.to_dict() for cp in self.checkpoint if cp.point is not Point.checkout}

        checkpoints.update(id=self.id,
                           package_checksum=self.package_checksum,
                           articlepkg_id=self.articlepkg_id,
                           started_at=str(self.started_at),
                           finished_at=str(self.finished_at) if self.finished_at else None,
                           collection_uri=self.collection_uri,
                           filepath=self.filepath,
                           is_valid=self.is_valid,)

        return checkpoints

    def __repr__(self):
        return "<Attempt('%s, %s')>" % (self.id, self.package_checksum)

    @classmethod
    def get_from_package(cls, package):
        """
        Get an Attempt for a package.

        :param package: instance of :class:`checkin.ArticlePackage`.
        """
        attempt = Attempt(package_checksum=package.checksum,
                          is_valid=False,
                          filepath=package._filename)
        meta = package.meta
        if package.is_valid_package() and (meta['journal_eissn'] or meta['journal_pissn']):
            attempt.is_valid = True
        return attempt


class ArticlePkg(Base):
    __tablename__ = 'articlepkg'

    id = Column(Integer, primary_key=True)
    article_title = Column(String, nullable=False)
    journal_pissn = Column(String, nullable=True)
    journal_eissn = Column(String, nullable=True)
    journal_title = Column(String, nullable=False)
    issue_year = Column(Integer, nullable=False)
    issue_volume = Column(String, nullable=True)
    issue_number = Column(String, nullable=True)
    issue_suppl_volume = Column(String, nullable=True)
    issue_suppl_number = Column(String, nullable=True)

    def to_dict(self):
        return dict(id=self.id,
                    article_title=self.article_title,
                    journal_pissn=self.journal_pissn,
                    journal_eissn=self.journal_eissn,
                    journal_title=self.journal_title,
                    issue_year=self.issue_year,
                    issue_volume=self.issue_volume,
                    issue_number=self.issue_number,
                    issue_suppl_volume=self.issue_suppl_volume,
                    issue_suppl_number=self.issue_suppl_number,
                    related_resources=[('attempts', 'Attempt', [attempt.id for attempt in self.attempts]),
                                       ('tickets', 'Ticket', [ticket.id for ticket in self.tickets]),
                            ]
                    )

    def __repr__(self):
        return "<ArticlePkg('%s, %s')>" % (self.id, self.article_title)

    @classmethod
    def get_or_create_from_package(cls, package, session):
        """
        Get or create an ArticlePkg for a package.

        :param package: instance of :class:`checkin.ArticlePackage`.
        :param session: sqlalchemy db session
        """
        meta = package.meta
        try:
            article_pkg = session.query(ArticlePkg).filter_by(article_title=meta['article_title']).one()
        except MultipleResultsFound as e:
            logger.error('Multiple results trying to get a models.ArticlePkg for article_title=%s. %s' % (
                meta['article_title'], e))

            raise ValueError('Multiple ArticlePkg for the given criteria')
        except NoResultFound as e:
            logger.debug('Creating a new models.ArticlePkg')

            article_pkg = ArticlePkg(**meta)

        return article_pkg


class Comment(Base):
    """
    Represents comments assigned to a :class:`Ticket`.
    """
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    author = Column(String, nullable=False)
    message = Column(String, nullable=False)
    ticket_id = Column(Integer, ForeignKey('ticket.id'))

    ticket = relationship('Ticket',
                          backref=backref('comments',
                          cascade='all, delete-orphan'))

    def __init__(self, *args, **kwargs):
        super(Comment, self).__init__(*args, **kwargs)
        self.date = datetime.datetime.now()

    def to_dict(self):
        return dict(message=self.message,
                    author=self.author,
                    date=str(self.date))

    def __repr__(self):
        return "<Comment('%s')>" % self.id


class Ticket(Base):
    """
    Represents an issue related to an :class:`ArticlePkg`.
    """
    __tablename__ = 'ticket'

    id = Column(Integer, primary_key=True)
    is_open = Column(Boolean)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    articlepkg_id = Column(Integer, ForeignKey('articlepkg.id'))
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    articlepkg = relationship('ArticlePkg',
                              backref=backref('tickets',
                              cascade='all, delete-orphan'))

    def __init__(self, *args, **kwargs):
        super(Ticket, self).__init__(*args, **kwargs)
        self.started_at = datetime.datetime.now()
        self.is_open = True

    def to_dict(self):
        return dict(id=self.id,
                    articlepkg_id=self.articlepkg_id,
                    is_open=self.is_open,
                    started_at=str(self.started_at),
                    finished_at=str(self.finished_at) if self.finished_at else None,
                    title=self.title,
                    author=self.author,
                    comments=[comment.to_dict() for comment in self.comments])

    def __repr__(self):
        return "<Ticket('%s')>" % self.id


##
# Represents system-wide checkpoints
##
class Point(enum.Enum):
    checkin = 1
    validation = 2
    checkout = 3


class Status(enum.Enum):
    ok = 1
    warning = 2
    error = 3


class Notice(Base):
    __tablename__ = 'notice'
    id = Column(Integer, primary_key=True)
    when = Column(DateTime(timezone=True))
    label = Column(String)
    message = Column(String, nullable=False)
    _status = Column('status', Integer, nullable=False)
    checkpoint_id = Column(Integer, ForeignKey('checkpoint.id'))

    def __init__(self, *args, **kwargs):
        # _status kwarg breaks sqlalchemy's default __init__
        _status = kwargs.pop('status', None)

        super(Notice, self).__init__(*args, **kwargs)
        self.when = datetime.datetime.now()

        if _status:
            self.status = _status

    @hybrid_property
    def status(self):
        return Status(self._status)

    @status.setter
    def status(self, st):
        self._status = st.value

    def to_dict(self):
        return dict(label=self.label,
                    message=self.message,
                    status=self.status.name,
                    date=str(self.when)
                    )


class Checkpoint(Base):
    __tablename__ = 'checkpoint'
    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    _point = Column('point', Integer, nullable=False)
    attempt_id = Column(Integer, ForeignKey('attempt.id'))
    messages = relationship('Notice',
                            order_by='Notice.when',
                            backref=backref('checkpoint'))
    attempt = relationship('Attempt',
                           backref=backref('checkpoint'))

    def __init__(self, point):
        """
        Represents a time delta of a checkpoint execution.

        i.e. the exact moment a module owns the package handling, until it ends.
        During this delta, arbitrary number of messages with meaningful data may
        be recorded.

        :param point: a known checkpoint, represented as :class:`Point`.
        """
        if point not in Point:
            raise ValueError('point must be %s' % ','.join(str(pt) for pt in Point))

        self.point = point
        self.started_at = self.ended_at = None

    def start(self):
        if self.started_at is None:
            self.started_at = datetime.datetime.now()

    def end(self):
        if self.ended_at is None:
            if not self.is_active:
                raise RuntimeError('end cannot be called before start')

            self.ended_at = datetime.datetime.now()

    @property
    def is_active(self):
        return bool(self.started_at and self.ended_at is None)

    def tell(self, message, status, label=None):
        if not self.is_active:
            raise RuntimeError('cannot tell thing after end was called')

        if status not in Status:
            raise ValueError('status must be %s' % ','.join(str(st) for st in Status))

        notice = Notice(message=message, status=status, label=label)
        self.messages.append(notice)

    @hybrid_property
    def point(self):
        return Point(self._point)

    @point.setter
    def point(self, pt):
        self._point = pt.value

    @point.expression
    def point(cls):
        return cls._point

    def to_dict(self):
        return dict(started_at=str(self.started_at),
                    finished_at=str(self.ended_at),
                    notices=[n.to_dict() for n in self.messages]
                        )

