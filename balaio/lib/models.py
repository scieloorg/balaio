#coding: utf-8
import datetime
import logging
import os

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
    event,
)
from sqlalchemy.orm import (
    relationship,
    backref,
    scoped_session,
    sessionmaker,
)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from zope.sqlalchemy import ZopeTransactionExtension

from .base28 import genbase
from .package import PackageAnalyzer


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
    debug_sql = config.getboolean('app', 'debug_sql')

    return create_engine(config.get('app', 'db_dsn'),
                         echo=debug_sql)


def init_database(engine):
    """
    Creates the database structure for the application.
    """
    Base.metadata.create_all(engine)

    # Load the Alembic configuration, and generate the version
    # table "stamping" it with the most recent revision.
    from alembic.config import Config
    from alembic import command

    try:
        config_path = os.environ['BALAIO_ALEMBIC_SETTINGS_FILE']
    except KeyError:
        logger.error('Missing BALAIO_ALEMBIC_SETTINGS_FILE env variable.')
    else:
        try:
            alembic_cfg = Config(config_path)
            command.stamp(alembic_cfg, "head")
        except IOError:
            logger.error('Could not find alembic config file at %s' % config_path)


class Attempt(Base):
    __tablename__ = 'attempt'

    id = Column(Integer, primary_key=True)
    package_checksum = Column(String(length=64), unique=True)
    articlepkg_id = Column(Integer, ForeignKey('articlepkg.id'), nullable=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    filepath = Column(String)
    is_valid = Column(Boolean)
    checkin_uri = Column(String(length=64), nullable=True)

    proceed_to_validation = Column(Boolean, nullable=False, default=False)
    validation_started_at = Column(DateTime(timezone=True))
    validation_ended_at = Column(DateTime(timezone=True))

    proceed_to_checkout = Column(Boolean, nullable=False)
    checkout_started_at = Column(DateTime)
    queued_checkout = Column(Boolean)

    articlepkg = relationship('ArticlePkg',
                              backref=backref('attempts',
                              cascade='all, delete-orphan'))

    def __init__(self, *args, **kwargs):
        super(Attempt, self).__init__(*args, **kwargs)
        self.started_at = datetime.datetime.now()
        self.is_valid = kwargs.get('is_valid', True)
        self.proceed_to_validation = kwargs.get('proceed_to_validation', False)
        self.proceed_to_checkout = kwargs.get('proceed_to_checkout', False)

    @property
    def analyzer(self):
        """
        Returns a PackageAnalyzer instance bound to the package.
        """
        p_analyzer = getattr(self, '_analyzer', None)
        if not p_analyzer:
            self._analyzer = PackageAnalyzer(self.filepath)

        return p_analyzer or self._analyzer

    def to_dict(self):

        checkpoints = {cp.point.name: cp.to_dict() for cp in self.checkpoint if cp.point is not Point.checkout}

        checkpoints.update(id=self.id,
                           package_checksum=self.package_checksum,
                           articlepkg_id=self.articlepkg_id,
                           started_at=str(self.started_at),
                           finished_at=str(self.finished_at) if self.finished_at else None,
                           filepath=self.filepath,
                           is_valid=self.is_valid,
                           proceed_to_checkout=self.proceed_to_checkout,
                           checkout_started_at=self.checkout_started_at,
                           queued_checkout=self.queued_checkout)

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
        if package.is_valid_package() and package.is_valid_meta() and package.is_valid_schema():
            attempt.is_valid = True
        return attempt

    @hybrid_method
    def ready_to_validate(self):
        """
        Returns a bool indicating if the attempt is ready to be validated.
        """
        return (self.proceed_to_validation == True) & (self.is_valid == True)

    def start_validation(self):
        """
        Mark the attempt validation as started.
        """
        self.proceed_to_validation = False
        self.validation_started_at = datetime.datetime.now()

    def end_validation(self):
        """
        Mark the attempt validation as ended.
        """
        self.validation_ended_at = datetime.datetime.now()

    @property
    def xml_filename(self):
        """
        Get the .xml file filename, used as identification by the operations team.

        If the filename has path data, these are ignored. e.g:
        0042-9686-bwho-91-08-545/0042-9686-bwho-91-08-545.xml returns
        0042-9686-bwho-91-08-545
        """
        xmls = self.analyzer.get_ext('xml')
        if len(xmls[:2]) == 1:
            xmlname = xmls[0].rsplit(os.sep, 1)[-1]
            return xmlname.rsplit(os.extsep, 1)[-2]
        else:
            raise ValueError('There are many xml files in the package.')


class ArticlePkg(Base):
    __tablename__ = 'articlepkg'

    id = Column(Integer, primary_key=True)
    aid = Column(String, nullable=False, index=True, unique=True)
    article_title = Column(String, nullable=False)
    journal_pissn = Column(String, nullable=True)
    journal_eissn = Column(String, nullable=True)
    journal_title = Column(String, nullable=False)
    issue_year = Column(Integer, nullable=False)
    issue_volume = Column(String, nullable=True)
    issue_number = Column(String, nullable=True)
    issue_suppl_volume = Column(String, nullable=True)
    issue_suppl_number = Column(String, nullable=True)

    @property
    def issue_label(self):
        """
        Return the issue label, some format can be return, see below:

        2014 (year, mandatory attribute)
        2014 N1 (year and number)
        2014 V31 (year and volume)
        2014 V31 N1 (year, volume and number)

        2014 suppl. V32 (year and supplement volume)
        2014 suppl. N23 (year and supplement number)
        2014 N4 suppl. N43 (year, number and supplement number)
        """

        suppl_volume = 'suppl. V%s' % self.issue_suppl_volume if self.issue_suppl_volume else ''
        suppl_number = 'suppl. N%s' % self.issue_suppl_number if self.issue_suppl_number else ''

        number = 'N%s' % self.issue_number if self.issue_number else ''

        volume = 'V%s' % self.issue_volume if self.issue_volume else ''

        values = [str(self.issue_year), volume, number, suppl_volume, suppl_number]

        return ' '.join([val for val in values if val]).strip()

    def get_aid(self):
        """
        Produce a fresh `aid` only for instances not yet persisted.
        """
        return self.aid if (self.id and self.aid) else genbase(10)

    def to_dict(self):
        return dict(
            id=self.id,
            aid=self.aid,
            article_title=self.article_title,
            journal_pissn=self.journal_pissn,
            journal_eissn=self.journal_eissn,
            journal_title=self.journal_title,
            issue_year=self.issue_year,
            issue_volume=self.issue_volume,
            issue_number=self.issue_number,
            issue_suppl_volume=self.issue_suppl_volume,
            issue_suppl_number=self.issue_suppl_number,
            related_resources=[('attempts', 'Attempt', [attempt.id for attempt in self.attempts]),],
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

    def __init__(self, point, **kwargs):
        """
        Represents a time delta of a checkpoint execution.

        i.e. the exact moment a module owns the package handling, until it ends.
        During this delta, arbitrary number of messages with meaningful data may
        be recorded.

        :param point: a known checkpoint, represented as :class:`Point`.
        """
        super(Checkpoint, self).__init__(**kwargs)

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


@event.listens_for(Session, 'before_flush')
def before_flush(session, flush_context, instances):
    # ArticlePkg.aid must be generated automaticaly while
    # a new instance is being saved.
    for obj in session.new:
        if isinstance(obj, ArticlePkg):
            # obj.aid must be unique, so we are checking for its absence
            # before assigning. This is not quite reliable by the lack
            # of atomicity over both the operations (query+assignment).
            for trial_no in range(10):
                aid = obj.get_aid()
                try:
                    session.query(ArticlePkg).filter_by(aid=aid).one()
                except NoResultFound:
                    break
                else:
                    logger.error("Conflict while generating ArticlePkg.aid attribute")
                    continue
            else:
                logger.error("Max attempts to generate an unique ArticlePkg.aid has expired. Giving up.")
                aid = None

            obj.aid = aid

