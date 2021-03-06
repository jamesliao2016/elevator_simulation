#!/usr/bin/env python
# encoding: utf-8


import unittest
from datetime import timedelta
from elevator_simulation.models import Floor, Person, Schedule


class TestPerson(unittest.TestCase):
    """Test person behavior and functionality."""

    def setUp(self):
        self.person = Person()

    def tearDown(self):
        pass

    def test_location(self):
        """tests that location setting works properly"""
        floor1 = Floor(level=1)
        floor2 = Floor(level=2)
        self.assertEqual(None, self.person.location)
        self.person.location = floor1
        self.assertEqual(floor1, self.person.location)
        self.person.location = floor2
        self.assertEqual(floor2, self.person.location)
        with self.assertRaises(TypeError):
            self.person.location = 2

    def test_max_stair_levels(self):
        """tests that stair level calculation is correct."""
        self.assertEqual(1, self.person.max_stair_levels_down)
        self.assertEqual(0, self.person.max_stair_levels_up)
        self.person = Person(fitness=10)
        self.assertEqual(10, self.person.max_stair_levels_down)
        self.assertEqual(9, self.person.max_stair_levels_up)


class TestSchedule(unittest.TestCase):
    """Test that the schedule can be properly manipulated"""

    def setUp(self):
        self.schedule = Schedule()
        self.floor = Floor(level=1)

    def tearDown(self):
        pass

    def test_add_event_bad_type(self):
        """tests that the right behavior occurs when adding an event with bad type."""
        with self.assertRaises(TypeError):
            self.schedule.add_event(12, self.floor)

    def test_add_event_bad_range(self):
        """tests that the right behavior occurs when adding an event with out of range time."""
        with self.assertRaises(ValueError):
            self.schedule.add_event(timedelta(days=2), self.floor)

        with self.assertRaises(ValueError):
            self.schedule.add_event(timedelta(days=1, microseconds=1), self.floor)

        with self.assertRaises(ValueError):
            self.schedule.add_event(timedelta(microseconds=-1), self.floor)

    def test_add_event_bad_location(self):
        """tests that the right behavior occurs when adding an event with bad location type."""
        with self.assertRaises(TypeError):
            self.schedule.add_event(timedelta(), None)

    def test_add_event(self):
        """tests that the right bheavior occurs when adding an event."""
        self.assertEqual(0, len(self.schedule.events))
        self.schedule.add_event(timedelta(hours=8, minutes=0), self.floor, "Go to work")
        self.assertEqual(1, len(self.schedule.events))

    def test_event_order(self):
        """tests that regardless of the event add order, the events are always in the right order."""
        self.schedule.add_event(timedelta(hours=1), self.floor)
        self.schedule.add_event(timedelta(hours=10), self.floor)
        self.schedule.add_event(timedelta(hours=5), self.floor)
        self.schedule.add_event(timedelta(hours=7), self.floor)
        self.schedule.add_event(timedelta(hours=3), self.floor)

        self.assertEqual(5, len(self.schedule.events))
        event = self.schedule.events[0]
        for next_event in self.schedule.events[1:]:
            self.assertLess(event, next_event)
            event = next_event
