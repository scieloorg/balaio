#coding: utf-8
import os
import sys
import stat
import zipfile
import itertools
import logging
import shutil
import uuid

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError
import transaction
from packtools import xray

import models
import utils
import excepts
import notifier

__all__ = ['PackageAnalyzer', 'get_attempt']
logger = logging.getLogger('balaio.checkin')


class PackageAnalyzer(xray.SPSPackage):

    def __init__(self, *args):
        super(PackageAnalyzer, self).__init__(*args)
        self._errors = set()
        self._default_perms = stat.S_IMODE(os.stat(self._filename).st_mode)
        self._is_locked = False

    def __enter__(self):
        self.lock_package()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.restore_perms()
        except OSError, exc:
            logger.info('The package had been deleted before the permissions restore procedure: %s' % exc)
        self._cleanup_package_fp()

    @property
    def meta(self):
        dct_mta = super(PackageAnalyzer, self).meta

        ign, dct_mta['issue_suppl_volume'], dct_mta['issue_number'], dct_mta['issue_suppl_number'] = utils.issue_identification(
            dct_mta['issue_volume'], dct_mta['issue_number'], dct_mta['supplement'])

        del dct_mta['supplement']

        return dct_mta

    @property
    def errors(self):
        """
        Returns a tuple of errors
        """
        return tuple(self._errors)

    def lock_package(self):
        """
         - Removes the write permission for Owners and Others
           http://docs.python.org/2/library/stat.html#stat.S_IWOTH
         - Change the group of package to the application group
           http://docs.python.org/2/library/os.html#os.chown
        """

        if not self._is_locked:
            perm = self._default_perms ^ stat.S_IWOTH ^ stat.S_IWUSR

            try:
                os.chmod(self._filename, perm)
            except OSError, e:
                self._errors.add(e.message)
                raise ValueError("Cant change the package permission")
            else:
                try:
                    os.chown(self._filename, -1, os.getgid())
                except OSError, e:
                    self.restore_perms()
                    self._errors.add(e.message)
                    raise ValueError("Cant change the group")

            self._is_locked = True

    def restore_perms(self):
        os.chmod(self._filename, self._default_perms)
        self._is_locked = False


class SafePackage(object):
    """
    Represents a package that can be inspected safely.

    The safety is obtained by copying the package to a
    working directory managed only by the application.
    """
    def __init__(self, package, working_dir):
        self.primary_path = package
        self.path = None
        self.working_dir = working_dir

        self._move_to_working_dir()

    def _gen_safe_path(self):
        basedir = os.path.dirname(self.primary_path)
        fname, fext = os.path.splitext(os.path.basename(self.primary_path))

        packid = uuid.uuid4().hex
        return os.path.join(self.working_dir, packid+fext)

    def _move_to_working_dir(self):
        new_path = self._gen_safe_path()
        shutil.copy2(self.primary_path, new_path)
        self.path = new_path

    @property
    def analyzer(self):
        """
        Returns a PackageAnalyzer instance bound to the package.
        """
        p_analyzer = getattr(self, '_analyzer', None)
        if not p_analyzer:
            self._analyzer = PackageAnalyzer(self.path)

        return p_analyzer or self._analyzer

    def mark_as_failed(self, silence=False):
        """
        Mark primary path as failed.

        If the target file is gone, the error is logged
        and the exception is silenced.
        """
        try:
            utils.mark_as_failed(self.primary_path)
        except OSError as e:
            logger.debug('The file is gone before marked as failed. %s' % e)
            if not silence: raise

    def mark_as_duplicated(self, silence=False):
        """
        Mark primary path as duplicated.

        If the target file if gone, the error is logged
        and the exception is silenced.
        """
        try:
            utils.mark_as_duplicated(self.primary_path)
        except OSError as e:
            logger.debug('The file is gone before marked as duplicated. %s' % e)
            if not silence: raise


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

                #checkin_notifier.tell('Attempt is valid.', models.Status.ok, 'Checkin')

            except Exception as e:
                savepoint.rollback()
                #checkin_notifier.tell('Failed to load an ArticlePkg for %s.' % package, models.Status.error, 'Checkin')

                logger.error('Failed to load an ArticlePkg for %s.' % package)
                logger.debug('---> Traceback: %s' % e)

            transaction.commit()
            return attempt

        except IOError as e:
            transaction.abort()
            logger.error('The package %s had been deleted during analysis' % package)
            logger.debug('---> Traceback: %s' % e)
            raise ValueError('The package %s had been deleted during analysis' % package)

        except IntegrityError as e:
            transaction.abort()
            logger.error('The package has no integrity. Aborting.')
            logger.debug('---> Traceback: %s' % e)

            if 'violates not-null constraint' in e.message:
                raise ValueError('An integrity error was cast as ValueError.')
            else:
                raise excepts.DuplicatedPackage('The package %s already exists.' % package)

        except Exception as e:
            transaction.abort()

            logger.error('Unexpected error! The package analysis for %s was aborted.' % (
                package))
            logger.debug('---> Traceback: %s' % e)
            raise ValueError('Unexpected error! The package analysis for %s was aborted.' % package)

        finally:
            logger.debug('Closing the transactional session scope')
            session.close()

