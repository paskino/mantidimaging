# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from io import StringIO

from mantidimaging.core.utility.leak_tracker import LeakTracker


class TestObject:
    pass


class TestContainer:
    def __init__(self, obj):
        self.held_reference = obj


class CommandLineArgumentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.leak_tracker = LeakTracker()

    def test_empty(self):
        self.assertEqual(self.leak_tracker.count(), 0)
        live_objects = self.leak_tracker.live_objects()
        self.assertEqual(len(list(live_objects)), 0)

    def test_add_object(self):
        self.assertEqual(self.leak_tracker.count(), 0)
        ob1 = TestObject()
        self.leak_tracker.add(ob1)
        self.assertEqual(self.leak_tracker.count(), 1)
        live_obs = [ob.ref() for ob in self.leak_tracker.live_objects()]
        self.assertIn(ob1, live_obs)

    def test_add_objects(self):
        self.assertEqual(self.leak_tracker.count(), 0)
        ob1 = TestObject()
        ob2 = TestObject()
        self.leak_tracker.add(ob1)
        self.leak_tracker.add(ob2)
        self.assertEqual(self.leak_tracker.count(), 2)

    def test_remove_objects(self):
        self.assertEqual(self.leak_tracker.count(), 0)
        ob1 = TestObject()
        ob2 = TestObject()
        ob3 = TestObject()
        self.leak_tracker.add(ob1)
        self.leak_tracker.add(ob2)
        self.leak_tracker.add(ob3)

        self.assertEqual(self.leak_tracker.count(), 3)

        del ob3
        self.assertEqual(self.leak_tracker.count(), 2)

    def test_tracking(self):
        self.assertEqual(self.leak_tracker.count(), 0)
        ob1 = TestObject()
        self.leak_tracker.add(ob1, "created_in_test_tracking")
        container = TestContainer(ob1)  # noqa: F841

        self.assertEqual(self.leak_tracker.count(), 1)
        del ob1
        self.assertEqual(self.leak_tracker.count(), 1)

        def check_output(message, **kwargs):
            track_output = StringIO()
            self.leak_tracker.pretty_print(output=track_output, **kwargs)
            track_output_value = track_output.getvalue()
            self.assertIn(message, track_output_value)

        # check that the object type and message are in the output
        check_output("leak_tracker_test.TestObject")
        check_output("created_in_test_tracking")

        # Check that this file and the line of code are listed in the output
        check_output(__file__, debug_init=True)
        check_output('self.leak_tracker.add(ob1, "created_in_test_tracking")', debug_init=True)

        # Check that container holding the reference is listed in the output
        check_output("leak_tracker_test.TestContainer", debug_owners=True)
        check_output("held_reference", debug_owners=True)
