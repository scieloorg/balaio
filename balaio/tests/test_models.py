import unittest
from datetime import datetime

import mocker
import enum

from balaio.models import (
    Point,
    Checkpoint,
    Status,
    Notice,
    Attempt,
    ArticlePkg,
)
from . import doubles


class CheckpointTests(unittest.TestCase):

    def test_type_must_be_known(self):
        chk_point = Checkpoint(Point.checkin)
        self.assertIsInstance(chk_point, Checkpoint)

    def test_unknown_type_raises_ValueError(self):
        class Color(enum.Enum):
            red = 1

        self.assertRaises(ValueError, lambda: Checkpoint(Color.red))

    def test_non_enum_type_raises_ValueError(self):
        self.assertRaises(ValueError, lambda: Checkpoint('foo'))

    def test_neutral_initial_state(self):
        chk_point = Checkpoint(Point.checkin)
        self.assertEqual(chk_point.started_at, None)
        self.assertEqual(chk_point.ended_at, None)

    def test_started_at_is_filled_on_start(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        self.assertIsInstance(chk_point.started_at, datetime)

    def test_start_is_idempotent(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        date1 = chk_point.started_at
        chk_point.start()
        date2 = chk_point.started_at

        self.assertEqual(date1, date2)

    def test_ended_at_is_filled_on_end(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.end()

        self.assertIsInstance(chk_point.ended_at, datetime)

    def test_end_is_idempotent(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.end()
        date1 = chk_point.ended_at
        chk_point.end()
        date2 = chk_point.ended_at

        self.assertEqual(date1, date2)

    def test_end_before_start_raises_RuntimeError(self):
        chk_point = Checkpoint(Point.checkin)
        self.assertRaises(RuntimeError, lambda: chk_point.end())

    def test_is_active_returns_False_on_initial_state(self):
        chk_point = Checkpoint(Point.checkin)
        self.assertEqual(chk_point.is_active, False)

    def test_is_active_returns_True_after_start(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        self.assertEqual(chk_point.is_active, True)

    def test_is_active_returns_False_after_end(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.end()
        self.assertEqual(chk_point.is_active, False)

    def test_tell_store_messages(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.tell('Foo', Status.ok)
        self.assertEqual(chk_point.messages[0].label, None)
        self.assertEqual(chk_point.messages[0].message, 'Foo')
        self.assertEqual(chk_point.messages[0].status, Status.ok)

    def test_tell_store_messages_based_on_labels(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.tell('Foo', Status.ok, label='zip')
        self.assertEqual(chk_point.messages[0].label, 'zip')
        self.assertEqual(chk_point.messages[0].message, 'Foo')
        self.assertEqual(chk_point.messages[0].status, Status.ok)

    def test_tell_raises_RuntimeError_on_inactive_objects(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.end()
        self.assertRaises(RuntimeError, lambda: chk_point.tell('Foo', Status.ok, label='zip'))


class NoticeTests(unittest.TestCase):

    def test_status_set_enum_values(self):
        ntc = Notice()
        ntc.status = Status.ok
        self.assertEqual(ntc.status, Status.ok)


class PointTests(unittest.TestCase):

    def test_required_enums(self):
        names = [pt.name for pt in Point]
        self.assertIn('checkin', names)
        self.assertIn('validation', names)
        self.assertIn('checkout', names)


class StatusTests(unittest.TestCase):

    def test_required_enums(self):
        names = [st.name for st in Status]
        self.assertIn('ok', names)
        self.assertIn('warning', names)
        self.assertIn('error', names)


class AttemptTests(mocker.MockerTestCase):

    def test_get_from_package(self):
        mock_session = self.mocker.mock()
        self.mocker.replay()
        pkg_analyzer = doubles.PackageAnalyzerStub()
        pkg_analyzer.is_valid_meta = lambda *args, **kwargs: True

        attempt = Attempt.get_from_package(pkg_analyzer)
        self.assertIsInstance(attempt, Attempt)

    def test_get_from_package_not_valid_for_missing_meta(self):
        mock_session = self.mocker.mock()
        self.mocker.replay()
        pkg_analyzer = doubles.PackageAnalyzerStub()
        pkg_analyzer.meta = {'journal_eissn': None, 'journal_pissn': None,
                            'article_title': None}
        pkg_analyzer.is_valid_meta = lambda *args, **kwargs: False

        attempt = Attempt.get_from_package(pkg_analyzer)
        self.assertFalse(attempt.is_valid)

    def test_get_from_package_not_valid_if_invalid(self):
        mock_session = self.mocker.mock()
        self.mocker.replay()
        pkg_analyzer = doubles.PackageAnalyzerStub()
        pkg_analyzer.meta = {'journal_eissn': '1234-1234', 'journal_pissn': '4321-1234'}
        pkg_analyzer.is_valid_meta = lambda *args, **kwargs: True
        pkg_analyzer.is_valid_package = lambda *args, **kwargs: False

        attempt = Attempt.get_from_package(pkg_analyzer)
        self.assertFalse(attempt.is_valid)

    def test_pending_checkout_must_ret_False_proceed_check_true_check_started_at_false(self):
        attempt = Attempt()
        attempt.proceed_to_checkout = True
        attempt.checkout_started_at = datetime.now()

        self.assertFalse(attempt.pending_checkout)

    def test_pending_checkout_must_ret_False_proceed_check_false_check_started_at_true(self):
        attempt = Attempt()
        attempt.proceed_to_checkout = False
        attempt.checkout_started_at = datetime.now()

        self.assertFalse(attempt.pending_checkout)

    def test_pending_checkout_must_ret_False_proceed_check_false_check_started_at_false(self):
        attempt = Attempt()
        attempt.proceed_to_checkout = False
        attempt.checkout_started_at = None

        self.assertFalse(attempt.pending_checkout)

    def test_pending_checkout_must_ret_True_proceed_check_true_check_started_at_false(self):
        attempt = Attempt()
        attempt.proceed_to_checkout = True
        attempt.checkout_started_at = None

        self.assertTrue(attempt.pending_checkout)


class ArticlePkgTests(mocker.MockerTestCase):

    def test_get_or_create_from_package(self):
        mock_session = self.mocker.mock()

        pkg_analyzer = doubles.PackageAnalyzerStub()
        pkg_analyzer.criteria = {'article_title': 'foo', 'journal_eissn':'1234-1234', 'journal_pissn':'1234-4321'}

        mock_session.query(ArticlePkg)
        self.mocker.result(mock_session)

        mock_session.filter_by(article_title='foo')
        self.mocker.result(mock_session)

        mock_session.one()
        self.mocker.result(ArticlePkg())

        self.mocker.replay()

        article_pkg = ArticlePkg.get_or_create_from_package(pkg_analyzer, mock_session)

        self.assertIsInstance(article_pkg, ArticlePkg)

