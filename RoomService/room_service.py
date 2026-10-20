# file: room_service.py
# purpose: Create, edit, and delete rooms and filter available rooms
# author: Su Pyae Pyae Aung (Micky)
# date: 2026-10-06

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Iterator, List, Optional

MIN_CAPACITY = 1


class RoomError(Exception):
    """Base class for all room service errors."""


class InvalidRoomError(RoomError):
    """Raised when room details are missing or not valid."""


class DuplicateRoomError(RoomError):
    """Raised when a room with the same id already exists."""


class RoomNotFoundError(RoomError):
    """Raised when a room id does not exist."""


@dataclass
class UnavailablePeriod:
    """A date range, inclusive at both ends, when a room cannot be used."""

    start_date: date
    end_date: date
    reason: str = ""


@dataclass
class Room:
    """A bookable room with its capacity, equipment, and closures."""

    room_id: str
    capacity: int
    equipment: Dict[str, int] = field(default_factory=dict)
    unavailable_periods: List[UnavailablePeriod] = field(
        default_factory=list
    )


def validate_room_details(
    room_id: str, capacity: int, equipment: Dict[str, int]
) -> None:
    """
    Check that room details are valid.

    Args:
        room_id (str): Identifier of the room, such as "A101".
        capacity (int): Maximum number of students the room holds.
        equipment (Dict[str, int]): Equipment name mapped to its count.

    Returns:
        None

    Raises:
        InvalidRoomError: If any detail is not valid.
    """
    if not room_id or not room_id.strip():
        raise InvalidRoomError("Room id must not be empty.")
    if isinstance(capacity, bool) or not isinstance(capacity, int):
        raise InvalidRoomError("Capacity must be a whole number.")
    if capacity < MIN_CAPACITY:
        raise InvalidRoomError("Capacity must be at least 1.")
    for name, count in equipment.items():
        if not name.strip():
            raise InvalidRoomError("Equipment name must not be empty.")
        if isinstance(count, bool) or not isinstance(count, int):
            raise InvalidRoomError("Equipment count must be a number.")
        if count < 0:
            raise InvalidRoomError("Equipment count must not be negative.")


def get_room(rooms: Dict[str, Room], room_id: str) -> Room:
    """
    Look up a room by id.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Id of the room to find.

    Returns:
        Room: The matching room.

    Raises:
        RoomNotFoundError: If no room has this id.
    """
    if room_id not in rooms:
        raise RoomNotFoundError(f"Room {room_id} does not exist.")
    return rooms[room_id]


def create_room(
    rooms: Dict[str, Room],
    room_id: str,
    capacity: int,
    equipment: Optional[Dict[str, int]] = None,
) -> Room:
    """
    Add a new room to the room data.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Unique id for the new room.
        capacity (int): Maximum number of students the room holds.
        equipment (Optional[Dict[str, int]]): Equipment name to count.

    Returns:
        Room: The room that was created.

    Raises:
        InvalidRoomError: If any detail is not valid.
        DuplicateRoomError: If the room id is already used.
    """
    equipment = dict(equipment or {})
    validate_room_details(room_id, capacity, equipment)
    if room_id in rooms:
        raise DuplicateRoomError(f"Room {room_id} already exists.")
    room = Room(room_id=room_id, capacity=capacity, equipment=equipment)
    rooms[room_id] = room
    return room


def edit_room(
    rooms: Dict[str, Room],
    room_id: str,
    capacity: Optional[int] = None,
    equipment: Optional[Dict[str, int]] = None,
) -> Room:
    """
    Change the capacity and/or equipment of an existing room.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Id of the room to edit.
        capacity (Optional[int]): New capacity, or None to keep it.
        equipment (Optional[Dict[str, int]]): New equipment, or None to
            keep it. When given, it replaces the old equipment.

    Returns:
        Room: The updated room.

    Raises:
        RoomNotFoundError: If the room does not exist.
        InvalidRoomError: If a new value is not valid.
    """
    room = get_room(rooms, room_id)
    new_capacity = room.capacity if capacity is None else capacity
    new_equipment = room.equipment if equipment is None else dict(equipment)
    validate_room_details(room_id, new_capacity, new_equipment)
    room.capacity = new_capacity
    room.equipment = new_equipment
    return room


def delete_room(rooms: Dict[str, Room], room_id: str) -> None:
    """
    Remove a room from the room data.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Id of the room to delete.

    Returns:
        None

    Raises:
        RoomNotFoundError: If the room does not exist.
    """
    get_room(rooms, room_id)
    del rooms[room_id]


def mark_room_unavailable(
    rooms: Dict[str, Room],
    room_id: str,
    start_date: date,
    end_date: date,
    reason: str = "",
) -> UnavailablePeriod:
    """
    Mark a room as unavailable from a start date to an end date.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Id of the room to close.
        start_date (date): First unavailable day.
        end_date (date): Last unavailable day (inclusive).
        reason (str): Why the room is unavailable, such as "Renovation".

    Returns:
        UnavailablePeriod: The period that was recorded.

    Raises:
        RoomNotFoundError: If the room does not exist.
        InvalidRoomError: If the end date is before the start date.
    """
    room = get_room(rooms, room_id)
    if end_date < start_date:
        raise InvalidRoomError("End date must not be before start date.")
    period = UnavailablePeriod(start_date, end_date, reason)
    room.unavailable_periods.append(period)
    return period


def is_room_available(room: Room, start_date: date, end_date: date) -> bool:
    """
    Check whether a room has no closure inside a date range.

    Args:
        room (Room): The room to check.
        start_date (date): First day needed.
        end_date (date): Last day needed (inclusive).

    Returns:
        bool: True if no unavailable period overlaps the range.
    """
    for period in room.unavailable_periods:
        # Both ranges are inclusive, so sharing a single day is a clash
        if start_date <= period.end_date and period.start_date <= end_date:
            return False
    return True


def has_equipment(room: Room, required: Dict[str, int]) -> bool:
    """
    Check whether a room has at least the required equipment counts.

    Args:
        room (Room): The room to check.
        required (Dict[str, int]): Equipment name to minimum count.

    Returns:
        bool: True if every required item is present in enough numbers.
    """
    for name, minimum in required.items():
        if room.equipment.get(name, 0) < minimum:
            return False
    return True


def validate_search(
    group_size: int, start_date: date, end_date: date
) -> None:
    """
    Check the inputs of a room search.

    Args:
        group_size (int): Number of students that must fit.
        start_date (date): First day the room is needed.
        end_date (date): Last day the room is needed (inclusive).

    Returns:
        None

    Raises:
        InvalidRoomError: If group size is below 1 or dates are reversed.
    """
    if group_size < MIN_CAPACITY:
        raise InvalidRoomError("Group size must be at least 1.")
    if end_date < start_date:
        raise InvalidRoomError("End date must not be before start date.")


def iter_matching_rooms(
    rooms: Dict[str, Room],
    group_size: int,
    start_date: date,
    end_date: date,
    required_equipment: Optional[Dict[str, int]] = None,
) -> Iterator[Room]:
    """
    Yield rooms that fit the group, have the equipment, and are open.

    Each room is checked once, so this is O(n) for n rooms.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        group_size (int): Number of students that must fit.
        start_date (date): First day the room is needed.
        end_date (date): Last day the room is needed (inclusive).
        required_equipment (Optional[Dict[str, int]]): Minimum equipment.

    Returns:
        Iterator[Room]: Matching rooms in the order they were added.
    """
    required = required_equipment or {}
    for room in rooms.values():
        if (
            room.capacity >= group_size
            and has_equipment(room, required)
            and is_room_available(room, start_date, end_date)
        ):
            yield room


def find_available_rooms(
    rooms: Dict[str, Room],
    group_size: int,
    start_date: date,
    end_date: date,
    required_equipment: Optional[Dict[str, int]] = None,
) -> List[Room]:
    """
    Filter rooms by capacity, equipment, and date range in O(n) time.

    Results are not sorted; the caller may sort them if it needs to.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        group_size (int): Number of students that must fit.
        start_date (date): First day the room is needed.
        end_date (date): Last day the room is needed (inclusive).
        required_equipment (Optional[Dict[str, int]]): Minimum equipment.

    Returns:
        List[Room]: Matching rooms in the order they were added.

    Raises:
        InvalidRoomError: If group size is below 1 or dates are reversed.
    """
    validate_search(group_size, start_date, end_date)
    return list(iter_matching_rooms(
        rooms, group_size, start_date, end_date, required_equipment
    ))


def recommend_room(
    rooms: Dict[str, Room],
    group_size: int,
    start_date: date,
    end_date: date,
    required_equipment: Optional[Dict[str, int]] = None,
) -> Optional[Room]:
    """
    Recommend the smallest matching room in one O(n) pass.

    A single pass with min() avoids the O(n log n) cost of sorting.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        group_size (int): Number of students that must fit.
        start_date (date): First day the room is needed.
        end_date (date): Last day the room is needed (inclusive).
        required_equipment (Optional[Dict[str, int]]): Minimum equipment.

    Returns:
        Optional[Room]: Smallest fitting room (ties broken by room id),
            or None if no room matches.

    Raises:
        InvalidRoomError: If group size is below 1 or dates are reversed.
    """
    validate_search(group_size, start_date, end_date)
    return min(
        iter_matching_rooms(
            rooms, group_size, start_date, end_date, required_equipment
        ),
        key=lambda room: (room.capacity, room.room_id),
        default=None,
    )
