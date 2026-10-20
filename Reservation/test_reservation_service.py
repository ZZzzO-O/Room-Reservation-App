# file: test_reservation_service.py
# purpose: Unit tests for reservation creation, editing, and conflicts
# author: Sittipruk Puttisarn (Jan)
# date: 2026-10-20
"""Tests for the reservation data layer and service."""

import unittest
from dataclasses import replace
from datetime import date, time
from typing import Dict, Optional


try:
    from .reservation_data import (
        DuplicateReservationError,
        Repetition,
        Reservation,
        ReservationNotFoundError,
        ReservationRepository,
    )
    from .reservation_service import (
        CapacityExceededError,
        InvalidReservationError,
        ReservationConflictError,
        ReservationService,
        RoomNotFoundError,
        has_time_overlap,
    )
except ImportError:
    from reservation_data import (
        DuplicateReservationError,
        Repetition,
        Reservation,
        ReservationNotFoundError,
        ReservationRepository,
    )
    from reservation_service import (
        CapacityExceededError,
        InvalidReservationError,
        ReservationConflictError,
        ReservationService,
        RoomNotFoundError,
        has_time_overlap,
    )


MONDAY = date(2026, 11, 2)
NEXT_MONDAY = date(2026, 11, 9)
TUESDAY = date(2026, 11, 3)
SEMESTER_END = date(2026, 12, 14)


class FakeRoomService:
    """Stand-in for the room service."""

    def __init__(self, capacities: Dict[str, int]) -> None:
        """
        Store the fake room capacities.

        Args:
            capacities (Dict[str, int]): Room ID to capacity.
        """
        self._capacities = capacities

    def get_room_capacity(self, room_id: str) -> Optional[int]:
        """
        Look up a fake room's capacity.

        Args:
            room_id (str): Room identifier.

        Returns:
            Optional[int]: Capacity, or None if the room is unknown.
        """
        return self._capacities.get(room_id)


def make_weekly(
    start_hour: int = 10,
    end_hour: int = 12,
    room_id: str = "R1",
    start_date: date = MONDAY,
    group_size: int = 20,
) -> Reservation:
    """
    Build a weekly reservation that runs until the semester ends.

    Args:
        start_hour (int): Start hour.
        end_hour (int): End hour.
        room_id (str): Room to reserve.
        start_date (date): First meeting date.
        group_size (int): Number of students.

    Returns:
        Reservation: A reservation without an ID.
    """
    return Reservation(
        competency="Databases",
        room_id=room_id,
        group_size=group_size,
        start_date=start_date,
        start_time=time(start_hour),
        end_time=time(end_hour),
        repetition=Repetition.WEEKLY,
        end_date=SEMESTER_END,
    )


def make_once(start_date: date, start_hour: int = 10) -> Reservation:
    """
    Build a one-off two-hour reservation in room R1.

    Args:
        start_date (date): Date of the meeting.
        start_hour (int): Start hour.

    Returns:
        Reservation: A reservation without an ID.
    """
    return replace(
        make_weekly(start_hour, start_hour + 2, start_date=start_date),
        repetition=Repetition.ONCE,
        end_date=None,
    )


class ReservationServiceTest(unittest.TestCase):
    """Tests for ReservationService."""

    def setUp(self) -> None:
        """Create a service with an empty repository."""
        self.repository = ReservationRepository()
        rooms = FakeRoomService({"R1": 30, "R2": 10})
        self.service = ReservationService(self.repository, rooms)

    def test_create_assigns_id(self) -> None:
        """A valid reservation is stored and given an ID."""
        saved = self.service.create_reservation(make_weekly())
        self.assertIsNotNone(saved.reservation_id)
        self.assertEqual(len(self.repository.get_all()), 1)

    def test_weekly_overlap_is_rejected(self) -> None:
        """Overlapping weekly slots in one room conflict."""
        self.service.create_reservation(make_weekly(10, 12))
        with self.assertRaises(ReservationConflictError):
            self.service.create_reservation(make_weekly(11, 13))

    def test_back_to_back_is_allowed(self) -> None:
        """A slot may start exactly when another ends."""
        self.service.create_reservation(make_weekly(10, 12))
        self.service.create_reservation(make_weekly(12, 14))

    def test_different_weekday_is_allowed(self) -> None:
        """The same time on another weekday is fine."""
        self.service.create_reservation(make_weekly(start_date=MONDAY))
        self.service.create_reservation(make_weekly(start_date=TUESDAY))

    def test_different_room_is_allowed(self) -> None:
        """The same slot in another room is fine."""
        self.service.create_reservation(make_weekly())
        self.service.create_reservation(
            make_weekly(room_id="R2", group_size=5)
        )

    def test_one_offs_on_different_dates_are_allowed(self) -> None:
        """One-off meetings on different Mondays do not clash."""
        self.service.create_reservation(make_once(MONDAY))
        self.service.create_reservation(make_once(NEXT_MONDAY))

    def test_one_off_inside_weekly_range_conflicts(self) -> None:
        """A one-off on a weekly meeting's day and time clashes."""
        self.service.create_reservation(make_weekly())
        with self.assertRaises(ReservationConflictError):
            self.service.create_reservation(make_once(NEXT_MONDAY))

    def test_one_off_after_weekly_range_is_allowed(self) -> None:
        """A one-off after the weekly meeting ends is fine."""
        self.service.create_reservation(make_weekly())
        self.service.create_reservation(make_once(date(2026, 12, 21)))

    def test_capacity_is_enforced(self) -> None:
        """A group larger than the room is rejected."""
        with self.assertRaises(CapacityExceededError):
            self.service.create_reservation(
                make_weekly(room_id="R2", group_size=11)
            )

    def test_unknown_room_is_rejected(self) -> None:
        """A missing room raises RoomNotFoundError."""
        with self.assertRaises(RoomNotFoundError):
            self.service.create_reservation(make_weekly(room_id="R99"))

    def test_invalid_fields_are_rejected(self) -> None:
        """Bad times, sizes, names, and dates are invalid."""
        bad_reservations = [
            make_weekly(12, 10),
            make_weekly(group_size=0),
            replace(make_weekly(), competency="  "),
            replace(make_weekly(), end_date=None),
            replace(make_weekly(), end_date=date(2026, 10, 1)),
        ]
        for reservation in bad_reservations:
            with self.assertRaises(InvalidReservationError):
                self.service.create_reservation(reservation)

    def test_edit_ignores_its_own_booking(self) -> None:
        """Extending a reservation does not clash with itself."""
        saved = self.service.create_reservation(make_weekly(10, 12))
        edited = self.service.edit_reservation(
            replace(saved, end_time=time(13))
        )
        self.assertEqual(edited.end_time, time(13))

    def test_edit_into_conflict_is_rejected(self) -> None:
        """Editing onto another booking's slot conflicts."""
        self.service.create_reservation(make_weekly(10, 12))
        later = self.service.create_reservation(make_weekly(13, 15))
        with self.assertRaises(ReservationConflictError):
            self.service.edit_reservation(
                replace(later, start_time=time(11))
            )

    def test_edit_missing_raises(self) -> None:
        """Editing an unknown ID raises ReservationNotFoundError."""
        with self.assertRaises(ReservationNotFoundError):
            self.service.edit_reservation(
                replace(make_weekly(), reservation_id="nope")
            )

    def test_delete_frees_the_slot(self) -> None:
        """A deleted reservation no longer blocks the room."""
        saved = self.service.create_reservation(make_weekly())
        self.service.delete_reservation(str(saved.reservation_id))
        self.service.create_reservation(make_weekly())

    def test_delete_missing_raises(self) -> None:
        """Deleting an unknown ID raises ReservationNotFoundError."""
        with self.assertRaises(ReservationNotFoundError):
            self.service.delete_reservation("nope")

    def test_search_by_competency(self) -> None:
        """Competency search is partial and case-insensitive."""
        self.service.create_reservation(make_weekly())
        self.assertEqual(len(self.service.search_by_competency("data")), 1)
        self.assertEqual(len(self.service.search_by_competency("math")), 0)

    def test_repository_rejects_duplicate_id(self) -> None:
        """Storing the same ID twice raises an error."""
        reservation = replace(make_weekly(), reservation_id="abc")
        self.repository.add_reservation(reservation)
        with self.assertRaises(DuplicateReservationError):
            self.repository.add_reservation(reservation)

    def test_has_time_overlap(self) -> None:
        """The overlap helper treats end times as exclusive."""
        self.assertTrue(
            has_time_overlap(time(9), time(11), time(10), time(11))
        )
        self.assertFalse(
            has_time_overlap(time(9), time(10), time(10), time(11))
        )


if __name__ == "__main__":
    unittest.main()
