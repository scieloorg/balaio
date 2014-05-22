#coding: utf-8
import logging

from sqlalchemy.exc import IntegrityError
import transaction

from . import models
from . import excepts


logger = logging.getLogger('balaio.checkin')


def get_attempt(package, Session=models.Session):
    """
    Returns a brand new models.Attempt instance, bound to a models.ArticlePkg
    instance.

    A package is valid when it has at least one valid xml file, according to
    SPS or rSPS xsd, and one pdf file.

    Case 1: Package is valid and has all needed metadata:
            A :class:`models.Attempt` is returned, bound to a :class:`models.ArticlePkg`.
    Case 2: Package is valid and doesn't have all needed metadata:
            A :class:`models.Attempt` is returned, with :attr:`models.Attempt.is_valid==False`.
    Case 3: Package is invalid
            A :class:`models.Attempt` is returned, with :attr:`models.Attempt.is_valid==False`.
    Case 4: Package is duplicated
            raises :class:`excepts.DuplicatedPackage`.

    :param package: Instance of SafePackage.
    :param Session: (optional) Reference to a Session class.
    """
    logger.info('Analyzing package: %s' % package)

    with package.analyzer as pkg:

        try:
            is_valid_xml = pkg.is_valid_schema()
        except AttributeError as e:  # if there is not a single xml file
            raise excepts.MissingXML(e.message)

        if not is_valid_xml:
            errors = pkg.stylechecker.validate()[1]
            exc_message = ['%s:%s %s' % (err.line, err.column, err.message) for err in errors]
            raise excepts.InvalidXML(exc_message)

        try:
            logger.debug('Creating a transactional session scope')
            session = Session()

            # Building a new Attempt
            attempt = models.Attempt.get_from_package(pkg)
            session.add(attempt)

            # Trying to bind a ArticlePkg
            savepoint = transaction.savepoint()
            try:
                article_pkg = models.ArticlePkg.get_or_create_from_package(pkg, session)
                if article_pkg not in session:
                    session.add(article_pkg)

                attempt.articlepkg = article_pkg
                attempt.is_valid = True

            except Exception as e:
                savepoint.rollback()
                logger.error('Failed to load an ArticlePkg for %s.' % package)
                logger.debug('---> Traceback: %s' % e)

            transaction.commit()
            return attempt

        except IntegrityError as e:
            transaction.abort()
            logger.debug('---> Traceback: %s' % e)

            if 'package_checksum' in e.message:
                raise excepts.DuplicatedPackage('The package %s already exists.' % package)
            else:
                raise

        except Exception as e:
            transaction.abort()
            logger.error('Something really bad happened while processing %s.' % package)
            logger.debug('---> Traceback: %s' % e)
            raise

        finally:
            logger.debug('Closing the transactional session scope')
            session.close()

