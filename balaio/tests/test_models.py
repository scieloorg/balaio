import unittest
from datetime import datetime

import enum

from balaio.models import Point, Checkpoint


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
        chk_point.tell('Foo')
        self.assertEqual(chk_point.messages[0].label, None)
        self.assertEqual(chk_point.messages[0].message, 'Foo')

    def test_tell_store_messages_based_on_labels(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.tell('Foo', label='zip')
        self.assertEqual(chk_point.messages[0].label, 'zip')
        self.assertEqual(chk_point.messages[0].message, 'Foo')

    def test_tell_raises_RuntimeError_on_inactive_objects(self):
        chk_point = Checkpoint(Point.checkin)
        chk_point.start()
        chk_point.end()
        self.assertRaises(RuntimeError, lambda: chk_point.tell('Foo', label='zip'))

