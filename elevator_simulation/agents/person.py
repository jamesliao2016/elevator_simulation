#!/usr/bin/env python
# encoding: utf-8

from datetime import timedelta
from elevator_simulation.agents import AgentMixin
from elevator_simulation.models import Person as PersonModel
import logging


logger = logging.getLogger(__name__)


def call_strategy_all(elevator_banks):
    return tuple(elevator_banks)


def call_strategy_random(elevator_banks):
    import random
    bank_index = random.randint(0, len(elevator_banks)-1)
    return (elevator_banks[bank_index], )


def default_trip_complete(trip):
    print(trip)


class ElevatorTrip(object):
    __slots__ = ("elevator_called_secs", "elevator_arrived_secs", "travel_secs", "person",
                 "start_location", "end_location", "event", "direction", "distance")
    """Docstring for ElevatorTrip. """

    def __init__(self):
        """TODO: to be defined1. """
        self.elevator_called_secs = None
        self.elevator_arrived_secs = None
        self.travel_secs = None
        self.person = None
        self.start_location = None
        self.end_location = None
        self.event = None
        self.direction = None
        self.distance = None

    def __str__(self):
        return ",".join([str(getattr(self, attr)) for attr in ElevatorTrip.__slots__])


class Person(AgentMixin, PersonModel):
    """Behavior for person agent"""
    person_id = 0

    def __repr__(self):
        return "<Person(id={})>".format(self.person_id)

    def __init__(self, sim, **kwargs):
        """creates a person agent that defines how an individual behaves.

        :param elevator_call_strategy func: The strategy to use when deciding the elevator bank to use.
        :param trip_complete func: The function to invoke when elevator arrives (def: logs)
        """
        AgentMixin.__init__(self, sim, events=["floor_reached", "elevator_door_open"])
        PersonModel.__init__(self, **kwargs)

        self.person_id = Person.person_id
        Person.person_id += 1
        self.action = self.env.process(self.run())
        self.call_strategy = kwargs.get("elevator_call_strategy", call_strategy_random)
        self.trip_complete = kwargs.get("trip_complete", default_trip_complete)

    def run(self):
        logger.debug("starting person agent for {}".format(self))
        # set the model location to the first floor
        self.location = self.simulation.building.floors[0]
        while True:
            now_td = timedelta(self.env.now)
            next_event = self.schedule.next_event(now_td)
            # if no event left, we are done
            if next_event is None:
                logger.debug("done with {}".format(self))
                break

            time_until_next_event = next_event.start_time - now_td

            # TODO: check if time is negative, if so, proceed directly without
            # waiting...
            # waits until the next event time
            logger.debug("{} waiting until {}".format(self, time_until_next_event.total_seconds()))
            yield self.env.timeout(time_until_next_event.total_seconds())
            logger.debug("{} resuming at {}".format(self, self.env.now))

            trip = ElevatorTrip()
            trip.person = self
            trip.event = next_event
            trip.start_location = self.location
            trip.end_location = trip.event.location
            trip.distance = self.location.distance(next_event.location)
            trip.direction = self.location.direction(next_event.location)
            # TODO: correct later to check for stairs
            # determine whether to take the steps or call the elevator
            # if elevator, call elevator and wait
            trip.elevator_called_secs = self.env.now
            elevator_banks = self.call_strategy(self.simulation.elevator_banks)
            logger.debug("{} chose {} elevator_bank(s) to call".format(self, len(elevator_banks)))
            for agent in elevator_banks:
                agent.wait(self, trip.start_location, trip.direction)
                agent.call_to(trip.start_location, trip.direction)

            # Wait until notified of elevator open door on floor
            event = self.event("elevator_door_open")
            yield event
            elevator_agent = event.value
            agent.stop_waiting(self, trip.start_location, trip.direction)
            trip.elevator_arrived_secs = self.env.now

            # TODO: update capacity
            elevator_agent.enter(self)
            elevator_agent.add_stop(trip.end_location)

            # TODO: need to wait for the elevator doors to open
            while elevator_agent.location != trip.end_location:
                yield self.event("elevator_door_open")
            elevator_agent.exit(self)

            trip.travel_secs = self.env.now - trip.elevator_arrived_secs
            self.location = trip.end_location  # we reached our location, yay!
            self.trip_complete(trip)

            # TODO: ELEVATOR: check that we ONLY stop when we are going in the
            # direction of the user (we'll get them on the way back)
