# coding: utf-8
import datetime

import enum
from sqlalchemy import (
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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


Session = sessionmaker(expire_on_commit=False)
Base = declarative_base()


def create_engine_from_config(config):
    """
    Create a sqlalchemy.engine using values from utils.Configuration.
    """
    return create_engine(config.get('app', 'db_dsn'),
                         echo=config.getboolean('app', 'debug'))


class Attempt(Base):
    __tablename__ = 'attempt'

    id = Column(Integer, primary_key=True)
    package_checksum = Column(String(length=32), unique=True)
    articlepkg_id = Column(Integer, ForeignKey('articlepkg.id'))
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
        self.is_valid = True

    def __repr__(self):
        return "<Attempt('%s, %s')>" % (self.id, self.package_checksum)


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

    def __repr__(self):
        return "<ArticlePkg('%s, %s')>" % (self.id, self.article_title)


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

