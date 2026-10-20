# file: reservation_data.py
# purpose: Store and manage detailed reservation information
# author: Sittipruk Puttisarn (Jan)
# date: 2026-10-20
"""Reservation model and in-memory storage for reservations."""

from dataclasses import dataclass
from datetime import date, time
from enum import Enum
from typing import Dict, List, Optional


class ReservationError(Exception):
    """Base class for all reservation errors."""


class DuplicateReservationError(ReservationError):
    """Raised when a reservation ID is already stored."""


class ReservationNotFoundError(ReservationError):
    """Raised when a requested reservation is not found."""


class DayOfWeek(Enum):
    """Days of the week, in the same order as date.weekday()."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class Repetition(Enum):
    """How often a reservation repeats."""

    ONCE = "Once"
    WEEKLY = "Weekly"


@dataclass
class Reservation:
    """
    A room reservation for one competency meeting.

    A ONCE reservation happens only on start_date. A WEEKLY reservation
    happens on every weekday matching start_date, up to and including
    end_date (for example, the last week of the semester).

    Attributes:
        competency (str): Competency name.
        room_id (str): Reserved room.
        group_size (int): Expected student count.
        start_date (date): First (or only) meeting date.
        start_time (time): Meeting start (inclusive).
        end_time (time): Meeting end (exclusive).
        repetition (Repetition): ONCE or WEEKLY.
        end_date (Optional[date]): Last date for WEEKLY reservations.
        reservation_id (Optional[str]): Assigned by the service.
    """

    competency: str
    room_id: str
    group_size: int
    start_date: date
    start_time: time
    end_time: time
    repetition: Repetition = Repetition.WEEKLY
    end_date: Optional[date] = None
    reservation_id: Optional[str] = None

    @property
    def day_of_week(self) -> DayOfWeek:
        """
        Weekday of the meeting, derived from start_date.

        Returns:
            DayOfWeek: The weekday the meeting falls on.
        """
        # Derived so the weekday can never disagree with the date
        return list(DayOfWeek)[self.start_date.weekday()]

    @property
    def last_date(self) -> date:
        """
        Last date on which the meeting can occur.

        Returns:
            date: end_date for weekly meetings, else start_date.
        """
        if self.repetition is Repetition.ONCE or self.end_date is None:
            return self.start_date
        return self.end_date


class ReservationRepository:
    """In-memory data access store for reservations."""

    def __init__(self) -> None:
        """Initialize an empty reservation storage dictionary."""
        self._reservations: Dict[str, Reservation] = {}

    def add_reservation(self, reservation: Reservation) -> Reservation:
        """
        Add a new reservation record to storage.

        Args:
            reservation (Reservation): The reservation to store. Its
                reservation_id must be set.

        Returns:
            Reservation: The stored reservation.

        Raises:
            ValueError: If the reservation has no ID.
            DuplicateReservationError: If the ID is already stored.
        """
        reservation_id = reservation.reservation_id
        if reservation_id is None:
            raise ValueError("Reservation must have an ID to be stored.")
        if reservation_id in self._reservations:
            raise DuplicateReservationError(
                f"Reservation ID '{reservation_id}' already exists."
            )
        self._reservations[reservation_id] = reservation
        return reservation

    def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """
        Fetch a reservation by its unique identifier.

        Args:
            reservation_id (str): Unique reservation ID.

        Returns:
            Optional[Reservation]: Reservation if found, else None.
        """
        return self._reservations.get(reservation_id)

    def get_by_room(self, room_id: str) -> List[Reservation]:
        """
        Fetch all reservations assigned to a specific room.

        Args:
            room_id (str): Room identifier.

        Returns:
            List[Reservation]: Reservations for the room.
        """
        return [
            reservation
            for reservation in self._reservations.values()
            if reservation.room_id == room_id
        ]

    def get_all(self) -> List[Reservation]:
        """
        Fetch every stored reservation.

        Returns:
            List[Reservation]: All reservations.
        """
        return list(self._reservations.values())

    def find_by_competency(self, text: str) -> List[Reservation]:
        """
        Find reservations whose competency name contains the text.

        Args:
            text (str): Part of a competency name (case-insensitive).

        Returns:
            List[Reservation]: Matching reservations.
        """
        wanted = text.strip().lower()
        return [
            reservation
            for reservation in self._reservations.values()
            if wanted in reservation.competency.lower()
        ]

    def update_reservation(self, reservation: Reservation) -> Reservation:
        """
        Replace an existing reservation record.

        Args:
            reservation (Reservation): Reservation with updates.

        Returns:
            Reservation: The updated reservation.

        Raises:
            ReservationNotFoundError: If the ID is not stored.
        """
        reservation_id = reservation.reservation_id
        if reservation_id is None or (
            reservation_id not in self._reservations
        ):
            raise ReservationNotFoundError(
                f"Reservation with ID '{reservation_id}' not found."
            )
        self._reservations[reservation_id] = reservation
        return reservation

    def delete_reservation(self, reservation_id: str) -> bool:
        """
        Delete a reservation from storage by ID.

        Args:
            reservation_id (str): Identifier of the reservation.

        Returns:
            bool: True if deleted, False if the ID was not found.
        """
        return self._reservations.pop(reservation_id, None) is not None
