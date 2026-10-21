# file: reservation_service.py
# purpose: Business logic for managing room reservations and conflict checks
# author: Sittipruk Puttisarn (Jan)
# date: 2026-10-20
"""Create, edit, and delete reservations with conflict detection."""

import uuid
from dataclasses import replace
from datetime import date, time, timedelta
from typing import List, Optional, Protocol

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


class InvalidReservationError(ReservationError):
    """Raised when reservation fields are missing or inconsistent."""


class RoomNotFoundError(ReservationError):
    """Raised when the room service does not know the room."""


class CapacityExceededError(ReservationError):
    """Raised when group size exceeds the room capacity."""


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


class RoomCapacityProvider(Protocol):
    """Interface the room service must offer to this service."""

    def get_room_capacity(self, room_id: str) -> Optional[int]:
        """
        Look up how many students a room holds.

        Args:
            room_id (str): Room identifier.

        Returns:
            Optional[int]: Capacity, or None if the room is unknown.
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
            CapacityExceededError: If the group does not fit.
            ReservationConflictError: If the room is already booked.
        """
        reservation_id = reservation.reservation_id
        if (
            reservation_id is None
            or self._repository.get_by_id(reservation_id) is None
        ):
            raise ReservationNotFoundError(
                f"Reservation with ID '{reservation_id}' not found."
            )
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
            raise ReservationNotFoundError(
                f"Reservation with ID '{reservation_id}' not found."
            )

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
            raise ReservationNotFoundError(
                f"Reservation with ID '{reservation_id}' not found."
            )
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
        week_end = week_start + timedelta(days=6)
        candidates = (
            self._repository.get_by_room(room_id)
            if room_id
            else self._repository.get_all()
        )
        matched = []
        for res in candidates:
            if has_date_overlap(
                res.start_date, res.last_date, week_start, week_end
            ):
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
            "=" * 79,
            "CMKL CLASSROOM RESERVATION SCHEDULE",
            f"Week: {week_start.isoformat()} to {week_end.isoformat()} "
            f"({room_label})",
            f"Total Bookings: {len(schedule)}",
            "=" * 79,
            f"{'Day':<10} {'Time':<15} {'Room':<10} {'Competency':<18} "
            f"{'Students':<10} {'Repetition'}",
            "-" * 79,
        ]

        if not schedule:
            lines.append("No reservations scheduled for this period.")
        else:
            for r in schedule:
                t_str = f"{r.start_time:%H:%M} - {r.end_time:%H:%M}"
                lines.append(
                    f"{r.day_of_week.value:<10} {t_str:<15} {r.room_id:<10} "
                    f"{r.competency:<18} {r.group_size:<10} "
                    f"{r.repetition.value}"
                )

        lines.append("=" * 79)
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
            CapacityExceededError: If the group does not fit.
            ReservationConflictError: If the room is already booked.
        """
        self._validate_fields(reservation)

        room_capacity = self._room_service.get_room_capacity(
            reservation.room_id
        )
        if room_capacity is None:
            raise RoomNotFoundError(
                f"Room '{reservation.room_id}' not found."
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
