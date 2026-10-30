# file: reservation_service.py
# purpose: Business logic for managing room reservations and conflict checks
# author: Sittipruk Puttisarn (Jan)
# date: 2026-10-20
"""Create, edit, and delete reservations with conflict detection."""

import uuid
from dataclasses import replace
from datetime import date, time, timedelta
from typing import List, Optional, Protocol

# Q7: we import the same 5 names twice, once as a
# package and once as a plain module. Works, but it's two lists to keep
# in sync.
# Fix idea: as a team, pick ONE way to run things (the gateway already
# puts Reservation/ on sys.path), then keep just one import block.
try:
    from .reservation_data import (
        Repetition,
        Reservation,
        ReservationError,
        ReservationNotFoundError,
        ReservationRepository,
    )
except ImportError:
    from reservation_data import (
        Repetition,
        Reservation,
        ReservationError,
        ReservationNotFoundError,
        ReservationRepository,
    )


ID_LENGTH = 8

# Plain-text schedule report layout (characters)
REPORT_WIDTH = 79
DAY_WIDTH = 10
TIME_WIDTH = 15
ROOM_WIDTH = 10
COMPETENCY_WIDTH = 18
STUDENTS_WIDTH = 10


class InvalidReservationError(ReservationError):
    """Raised when reservation fields are missing or inconsistent."""


class RoomNotFoundError(ReservationError):
    """Raised when the room service does not know the room."""


class CapacityExceededError(ReservationError):
    """Raised when group size exceeds the room capacity."""


class RoomUnavailableError(ReservationError):
    """Raised when the room is closed (e.g. renovation) during the booking."""


class RoomClosureConflictError(ReservationError):
    """Raised when a proposed closure overlaps an existing reservation."""

    def __init__(
        self, reservation: Reservation, conflict_date: date
    ) -> None:
        self.reservation = reservation
        self.conflict_date = conflict_date
        super().__init__(
            f"Cannot close the room: reservation {reservation.reservation_id} "
            f"({reservation.competency}) is booked for "
            f"{conflict_date.isoformat()} from "
            f"{reservation.start_time.strftime('%H:%M')} to "
            f"{reservation.end_time.strftime('%H:%M')}. "
            "Move or cancel this booking first."
        )


# Q8: flake8-bugbear flags this (B042): super() only gets
# `message`, so copy/pickle can't rebuild the error. Heads-up: the obvious
# fix super().__init__(message, conflicting_reservation) makes str(err) a
# tuple and breaks the gateway's error text. Fine to leave + note why.
class ReservationConflictError(ReservationError):
    """Raised when a candidate overlaps an existing reservation."""

    def __init__(
        self, message: str, conflicting_reservation: Reservation
    ) -> None:
        """
        Store the reservation that caused the conflict.

        Args:
            message (str): Human-readable description.
            conflicting_reservation (Reservation): The existing clash.
        """
        super().__init__(message)
        self.conflicting_reservation = conflicting_reservation


def _reservation_not_found(
    reservation_id: Optional[str],
) -> ReservationNotFoundError:
    """
    Build the error used whenever a reservation ID is not stored.

    Args:
        reservation_id (Optional[str]): The ID that was looked up.

    Returns:
        ReservationNotFoundError: Error ready to be raised.
    """
    return ReservationNotFoundError(
        f"Reservation with ID '{reservation_id}' not found."
    )


class RoomCapacityProvider(Protocol):  # pylint: disable=too-few-public-methods
    """Interface the room service must offer to this service."""

    def get_room_capacity(self, room_id: str) -> Optional[int]:
        """
        Look up how many students a room holds.

        Args:
            room_id (str): Room identifier.

        Returns:
            Optional[int]: Capacity, or None if the room is unknown.
        """

    def is_room_available(
        self, room_id: str, start_date: date, end_date: date
    ) -> bool:
        """
        Check that a room is not closed on any day in a date range.

        Args:
            room_id (str): Room identifier.
            start_date (date): First day needed.
            end_date (date): Last day needed (inclusive).

        Returns:
            bool: False if the room is unknown or closed in that range.
        """


def is_room_big_enough(capacity: int, group_size: int) -> bool:
    """
    Check whether a room can fit a group.

    Args:
        capacity (int): Maximum number of students the room holds.
        group_size (int): Number of students in the group.

    Returns:
        bool: True if the group fits in the room.
    """
    return group_size <= capacity


def has_time_overlap(
    start: time, end: time, existing_start: time, existing_end: time
) -> bool:
    """
    Check whether two time slots overlap.

    Args:
        start (time): Start of the candidate slot.
        end (time): End of the candidate slot.
        existing_start (time): Start of the existing slot.
        existing_end (time): End of the existing slot.

    Returns:
        bool: True if the slots share any time.
    """
    # Slots are [start, end), so 10:00-12:00 does not block 12:00-14:00
    return start < existing_end and existing_start < end


def has_date_overlap(
    first_start: date, first_end: date, second_start: date, second_end: date
) -> bool:
    """
    Check whether two inclusive date ranges overlap.

    Args:
        first_start (date): First day of the first range.
        first_end (date): Last day of the first range.
        second_start (date): First day of the second range.
        second_end (date): Last day of the second range.

    Returns:
        bool: True if the ranges share any day.
    """
    return first_start <= second_end and second_start <= first_end


# GOOOD: really neat. Same weekday + overlapping date ranges means they
# DO share a real meeting date (the later start date is one), so no need to
# loop over every week. We checked it, the comment is right.
def is_conflicting(first: Reservation, second: Reservation) -> bool:
    """
    Check whether two reservations ever need the same room at once.

    Args:
        first (Reservation): One reservation.
        second (Reservation): Another reservation.

    Returns:
        bool: True if they share a room, weekday, date, and time.
    """
    # Same weekday plus overlapping date ranges guarantees a shared date
    return (
        first.room_id == second.room_id
        and first.day_of_week == second.day_of_week
        and has_date_overlap(
            first.start_date,
            first.last_date,
            second.start_date,
            second.last_date,
        )
        and has_time_overlap(
            first.start_time,
            first.end_time,
            second.start_time,
            second.end_time,
        )
    )


def conflicts_with_closure(
    reservation: Reservation, closure_start: date, closure_end: date
) -> bool:
    """
    Check whether any meeting date of a reservation falls within a closure.

    Args:
        reservation (Reservation): The reservation to test.
        closure_start (date): First day of the room closure.
        closure_end (date): Last day of the room closure (inclusive).

    Returns:
        bool: True if at least one meeting date overlaps the closure.
    """
    return first_meeting_in_closure(
        reservation, closure_start, closure_end
    ) is not None


def first_meeting_in_closure(
    reservation: Reservation, closure_start: date, closure_end: date
) -> Optional[date]:
    """Return the first actual meeting date inside a closure, if any."""
    if reservation.repetition is Repetition.ONCE:
        if closure_start <= reservation.start_date <= closure_end:
            return reservation.start_date
        return None

    overlap_start = max(reservation.start_date, closure_start)
    overlap_end = min(reservation.last_date, closure_end)
    if overlap_start > overlap_end:
        return None

    target_weekday = reservation.start_date.weekday()
    days_until_meeting = (target_weekday - overlap_start.weekday()) % 7
    meeting_date = overlap_start + timedelta(days=days_until_meeting)
    return meeting_date if meeting_date <= overlap_end else None


class ReservationService:
    """Service handling CRUD operations and validation for reservations."""

    def __init__(
        self,
        repository: ReservationRepository,
        room_service: RoomCapacityProvider,
    ) -> None:
        """
        Initialize the service.

        Args:
            repository (ReservationRepository): Reservation storage.
            room_service (RoomCapacityProvider): The room service.
        """
        self._repository = repository
        self._room_service = room_service

# GOOOD: clean split. _validate_fields() needs nothing else, then room
# checks, then conflicts. create and edit share the same checks.
    def create_reservation(self, reservation: Reservation) -> Reservation:
        """
        Validate a new reservation, give it an ID, and store it.

        Args:
            reservation (Reservation): Candidate; its ID is ignored.

        Returns:
            Reservation: The stored reservation with its new ID.

        Raises:
            InvalidReservationError: If a field is invalid.
            RoomNotFoundError: If the room does not exist.
            RoomUnavailableError: If the room is closed in that period.
            CapacityExceededError: If the group does not fit.
            ReservationConflictError: If the room is already booked.
        """
        new_reservation = replace(
            reservation, reservation_id=self._generate_reservation_id()
        )
        self._validate_reservation(new_reservation)
        return self._repository.add_reservation(new_reservation)

    def edit_reservation(self, reservation: Reservation) -> Reservation:
        """
        Validate changes to an existing reservation and save them.

        Args:
            reservation (Reservation): Updated reservation with its ID.

        Returns:
            Reservation: The saved reservation.

        Raises:
            ReservationNotFoundError: If the ID is not stored.
            InvalidReservationError: If a field is invalid.
            RoomNotFoundError: If the room does not exist.
            RoomUnavailableError: If the room is closed in that period.
            CapacityExceededError: If the group does not fit.
            ReservationConflictError: If the room is already booked.
        """
        reservation_id = reservation.reservation_id
        if (
            reservation_id is None
            or self._repository.get_by_id(reservation_id) is None
        ):
            raise _reservation_not_found(reservation_id)
        self._validate_reservation(reservation)
        return self._repository.update_reservation(reservation)

    def delete_reservation(self, reservation_id: str) -> None:
        """
        Delete an existing reservation by ID.

        Args:
            reservation_id (str): Reservation ID.

        Raises:
            ReservationNotFoundError: If the ID is not stored.
        """
        if not self._repository.delete_reservation(reservation_id):
            raise _reservation_not_found(reservation_id)

    def cancel_reservations_for_closure(
        self, room_id: str, start_date: date, end_date: date
    ) -> List[Reservation]:
        """
        Cancel all reservations in a room overlapping an unavailable range.

        Args:
            room_id (str): Room identifier.
            start_date (date): First day of closure.
            end_date (date): Last day of closure (inclusive).

        Returns:
            List[Reservation]: The reservations that were cancelled.

        Raises:
            ValueError: If end_date is before start_date.
        """
        if end_date < start_date:
            raise ValueError("End date must not be before start date.")
        conflicted = [
            res
            for res in self._repository.get_by_room(room_id)
            if conflicts_with_closure(res, start_date, end_date)
        ]
        for res in conflicted:
            if res.reservation_id is not None:
                self._repository.delete_reservation(res.reservation_id)
        return conflicted

    def get_reservation(self, reservation_id: str) -> Reservation:
        """
        Fetch one reservation.

        Args:
            reservation_id (str): Reservation ID.

        Returns:
            Reservation: The matching reservation.

        Raises:
            ReservationNotFoundError: If the ID is not stored.
        """
        reservation = self._repository.get_by_id(reservation_id)
        if reservation is None:
            raise _reservation_not_found(reservation_id)
        return reservation

    def search_by_competency(self, text: str) -> List[Reservation]:
        """
        Find reservations by part of the competency name.

        Args:
            text (str): Part of a competency name.

        Returns:
            List[Reservation]: Matching reservations.
        """
        return self._repository.find_by_competency(text)

    def get_all_reservations(self) -> List[Reservation]:
        """
        Fetch all stored reservations.

        Returns:
            List[Reservation]: All reservations in storage.
        """
        return self._repository.get_all()

    def validate_room_closure(
        self, room_id: str, start_date: date, end_date: date
    ) -> None:
        """Reject a closure if any existing room booking meets in its range."""
        if end_date < start_date:
            raise ValueError("End date must not be before start date.")
        for reservation in self._repository.get_by_room(room_id):
            conflict_date = first_meeting_in_closure(
                reservation, start_date, end_date
            )
            if conflict_date:
                raise RoomClosureConflictError(reservation, conflict_date)

    def get_schedule(
        self, week_start: date, room_id: Optional[str] = None
    ) -> List[Reservation]:
        """
        Fetch reservations active during the specified week.

        Args:
            week_start (date): Start date of the week (e.g. Monday).
            room_id (Optional[str]): If provided, filter for this room only.

        Returns:
            List[Reservation]: Active reservations sorted by day and time.
        """
        candidates = (
            self._repository.get_by_room(room_id)
            if room_id
            else self._repository.get_all()
        )
        matched = []
        for res in candidates:
            # A reservation meets at most once a week, so find that date
            # and keep the reservation only if it falls inside its range
            offset = (res.start_date.weekday() - week_start.weekday()) % 7
            meeting_day = week_start + timedelta(days=offset)
            if res.start_date <= meeting_day <= res.last_date:
                matched.append(res)

        # Sort by weekday, start_time, room_id
        matched.sort(
            key=lambda r: (r.start_date.weekday(), r.start_time, r.room_id)
        )
        return matched

    def export_schedule_text(
        self, week_start: date, room_id: Optional[str] = None
    ) -> str:
        """
        Export weekly schedule to formatted plain text report.

        Args:
            week_start (date): Start date of the target week.
            room_id (Optional[str]): Room identifier or None for all rooms.

        Returns:
            str: Human-readable formatted timetable text.
        """
        schedule = self.get_schedule(week_start, room_id)
        week_end = week_start + timedelta(days=6)
        room_label = f"Room: {room_id}" if room_id else "All Rooms"

        lines = [
            "=" * REPORT_WIDTH,
            "CMKL CLASSROOM RESERVATION SCHEDULE",
            f"Week: {week_start.isoformat()} to {week_end.isoformat()} "
            f"({room_label})",
            f"Total Bookings: {len(schedule)}",
            "=" * REPORT_WIDTH,
            f"{'Day':<{DAY_WIDTH}} {'Time':<{TIME_WIDTH}} "
            f"{'Room':<{ROOM_WIDTH}} {'Competency':<{COMPETENCY_WIDTH}} "
            f"{'Students':<{STUDENTS_WIDTH}} {'Repetition'}",
            "-" * REPORT_WIDTH,
        ]

        if not schedule:
            lines.append("No reservations scheduled for this period.")
        else:
            for r in schedule:
                t_str = f"{r.start_time:%H:%M} - {r.end_time:%H:%M}"
                name = r.competency[:COMPETENCY_WIDTH]
                lines.append(
                    f"{r.day_of_week.value:<{DAY_WIDTH}} "
                    f"{t_str:<{TIME_WIDTH}} {r.room_id:<{ROOM_WIDTH}} "
                    f"{name:<{COMPETENCY_WIDTH}} "
                    f"{r.group_size:<{STUDENTS_WIDTH}} "
                    f"{r.repetition.value}"
                )

        lines.append("=" * REPORT_WIDTH)
        return "\n".join(lines)

    def _generate_reservation_id(self) -> str:
        """
        Create a short ID that is not already in use.

        Returns:
            str: A new unique reservation ID.
        """
        reservation_id = uuid.uuid4().hex[:ID_LENGTH]
        while self._repository.get_by_id(reservation_id) is not None:
            reservation_id = uuid.uuid4().hex[:ID_LENGTH]
        return reservation_id

    def _validate_reservation(self, reservation: Reservation) -> None:
        """
        Run every check a reservation must pass before it is saved.

        Args:
            reservation (Reservation): Candidate reservation.

        Raises:
            InvalidReservationError: If a field is invalid.
            RoomNotFoundError: If the room does not exist.
            RoomUnavailableError: If the room is closed in that period.
            CapacityExceededError: If the group does not fit.
            ReservationConflictError: If the room is already booked.
        """
# Q4: nothing stops a booking in 2030, or last year.
# Test plan 5.11 expects "outside the semester" to be rejected.
# Decide: add SEMESTER_START / SEMESTER_END and check here, or drop that test.
        self._validate_fields(reservation)

        room_capacity = self._room_service.get_room_capacity(
            reservation.room_id
        )
        if room_capacity is None:
            raise RoomNotFoundError(
                f"Room '{reservation.room_id}' not found."
            )
        # Checked after the lookup above because an unknown room also
        # reports "not available", and that case needs its own error
        if not self._room_service.is_room_available(
            reservation.room_id, reservation.start_date, reservation.last_date
        ):
            raise RoomUnavailableError(
                f"Room '{reservation.room_id}' is unavailable between "
                f"{reservation.start_date.isoformat()} and "
                f"{reservation.last_date.isoformat()}."
            )
        if not is_room_big_enough(room_capacity, reservation.group_size):
            raise CapacityExceededError(
                f"Room capacity ({room_capacity}) is smaller "
                f"than group size ({reservation.group_size})."
            )

        existing = self._find_conflict(reservation)
        if existing is not None:
            raise ReservationConflictError(
                f"Time conflict with existing reservation "
                f"({existing.competency}: {existing.day_of_week.value} "
                f"{existing.start_time:%H:%M}-{existing.end_time:%H:%M}).",
                existing,
            )

    def _find_conflict(
        self, reservation: Reservation
    ) -> Optional[Reservation]:
        """
        Find an existing reservation that clashes with a candidate.

        Args:
            reservation (Reservation): Candidate reservation.

        Returns:
            Optional[Reservation]: The first clash, or None.
        """
        for existing in self._repository.get_by_room(reservation.room_id):
            # A reservation never conflicts with its own saved version
            if existing.reservation_id == reservation.reservation_id:
                continue
            if is_conflicting(reservation, existing):
                return existing
        return None

    @staticmethod
    def _validate_fields(reservation: Reservation) -> None:
        """
        Check fields that need neither the room nor other reservations.

        Args:
            reservation (Reservation): Candidate reservation.

        Raises:
            InvalidReservationError: If a field is invalid.
        """
        if not reservation.competency.strip():
            raise InvalidReservationError("Competency name is required.")
        if reservation.group_size <= 0:
            raise InvalidReservationError("Group size must be positive.")
        if reservation.start_time >= reservation.end_time:
            raise InvalidReservationError("End time must be after start.")
        if reservation.repetition is Repetition.WEEKLY:
            if reservation.end_date is None:
                raise InvalidReservationError(
                    "Weekly reservations need an end date."
                )
            if reservation.end_date < reservation.start_date:
                raise InvalidReservationError(
                    "End date must not be before start date."
                )
        elif reservation.end_date not in (None, reservation.start_date):
            raise InvalidReservationError(
                "One-time reservations cannot have a different end date."
            )
