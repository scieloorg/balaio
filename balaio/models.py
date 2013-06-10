# coding: utf-8
import datetime

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    String,
)
from sqlalchemy.orm import (
    relationship,
    backref,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)


Base = declarative_base()


class Attempt(Base):
    __tablename__ = 'attempt'

    id = Column(Integer, primary_key=True)
    package_md5 = Column(String(length=32), unique=True)
    articlepkg_id = Column(Integer, ForeignKey('articlepkg.id'))
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    collection_uri = Column(String)

    articlepkg = relationship('ArticlePkg',
                              backref=backref('attempts',
                              cascade='all, delete-orphan'))

    def __init__(self, *args, **kwargs):
        super(Attempt, self).__init__(*args, **kwargs)
        self.started_at = datetime.datetime.now()

    def __repr__(self):
        return "<Attempt('%s, %s')>" % (self.id, self.package_md5)


class ArticlePkg(Base):
    __tablename__ = 'articlepkg'

    id = Column(Integer, primary_key=True)
    article_title = Column(String, nullable=False)
    journal_pissn = Column(String, nullable=False)
    journal_eissn = Column(String, nullable=False)
    journal_title = Column(String, nullable=False)
    issue_year = Column(Integer, nullable=False)
    issue_volume = Column(Integer, nullable=False)
    issue_number = Column(Integer, nullable=False)

    def __repr__(self):
        return "<ArticlePkg('%s, %s')>" % (self.id, self.article_title)


def get_or_create(model, **kwargs):
        """
        Try get the model by ```kwargs``` otherwise create the model.
        """
        ses = Session()

        obj = ses.query(model).filter_by(**kwargs)

        if ses.query(obj.exists()).scalar():
            return obj.one()
        else:
            obj = model(**kwargs)
            ses.add(obj)
            ses.commit()
            return obj


if __name__ == '__main__':
    import sys

    # Create the DB structure
    if 'syncdb' in sys.argv:
        Base.metadata.create_all(engine)
