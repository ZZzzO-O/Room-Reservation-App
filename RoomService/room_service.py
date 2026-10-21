# file: room_service.py
# purpose: Create, edit, and delete rooms and filter available rooms
# author: Su Pyae Pyae Aung (Micky)
# date: 2026-10-06
"""Room Service business logic for managing classrooms and availability."""


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


@dataclass(slots=True)
class UnavailablePeriod:
    """A date range, inclusive at both ends, when a room cannot be used."""

    start_date: date
    end_date: date
    reason: str = ""


@dataclass(slots=True)
class Room:
    """A bookable room with its capacity, equipment, and closures."""

    room_id: str
    capacity: int
    name: str = ""
    equipment: Dict[str, int] = field(default_factory=dict)
    unavailable_periods: List[UnavailablePeriod] = field(
        default_factory=list
    )


def validate_room_details(
    room_id: str,
    capacity: int,
    equipment: Dict[str, int],
    name: str = "",
) -> None:
    """
    Check that room details are valid.

    Args:
        room_id (str): Identifier of the room, such as "601" or "A101".
        capacity (int): Maximum number of students the room holds.
        equipment (Dict[str, int]): Equipment name mapped to its count.
        name (str): Optional human-readable room name (e.g., "Pioneer").

    Returns:
        None

    Raises:
        InvalidRoomError: If any detail is not valid.
    """
    if not isinstance(room_id, str) or not room_id.strip():
        raise InvalidRoomError("Room id must not be empty.")
    if isinstance(capacity, bool) or not isinstance(capacity, int):
        raise InvalidRoomError("Capacity must be a whole number.")
    if capacity < MIN_CAPACITY:
        raise InvalidRoomError("Capacity must be at least 1.")
    if not isinstance(name, str):
        raise InvalidRoomError("Room name must be a string.")
    for item_name, count in equipment.items():
        if not isinstance(item_name, str) or not item_name.strip():
            raise InvalidRoomError("Equipment name must not be empty.")
        if isinstance(count, bool) or not isinstance(count, int):
            raise InvalidRoomError("Equipment count must be a number.")
        if count < 0:
            raise InvalidRoomError("Equipment count must not be negative.")


def get_room(rooms: Dict[str, Room], room_id: str) -> Room:
    """
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
    name: str = "",
) -> Room:
    """
    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Unique id for the new room.
        capacity (int): Maximum number of students the room holds.
        equipment (Optional[Dict[str, int]]): Equipment name to count.
        name (str): Optional name of the room (e.g., "Pioneer").

    Returns:
        Room: The room that was created.

    Raises:
        InvalidRoomError: If any detail is not valid.
        DuplicateRoomError: If the room id is already used.
    """
    clean_equipment = dict(equipment or {})
    validate_room_details(room_id, capacity, clean_equipment, name)
    if room_id in rooms:
        raise DuplicateRoomError(f"Room {room_id} already exists.")
    room = Room(
        room_id=room_id,
        capacity=capacity,
        name=name,
        equipment=clean_equipment,
    )
    rooms[room_id] = room
    return room


def edit_room(
    rooms: Dict[str, Room],
    room_id: str,
    capacity: Optional[int] = None,
    equipment: Optional[Dict[str, int]] = None,
    name: Optional[str] = None,
) -> Room:
    """
    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        room_id (str): Id of the room to edit.
        capacity (Optional[int]): New capacity, or None to keep it.
        equipment (Optional[Dict[str, int]]): New equipment, or None to
            keep it. When given, it replaces the old equipment.
        name (Optional[str]): New room name, or None to keep it.

    Returns:
        Room: The updated room.

    Raises:
        RoomNotFoundError: If the room does not exist.
        InvalidRoomError: If a new value is not valid.
    """
    room = get_room(rooms, room_id)
    new_capacity = room.capacity if capacity is None else capacity
    new_equipment = (
        room.equipment if equipment is None else dict(equipment)
    )
    new_name = room.name if name is None else name
    validate_room_details(room_id, new_capacity, new_equipment, new_name)
    room.capacity = new_capacity
    room.equipment = new_equipment
    room.name = new_name
    return room


def delete_room(rooms: Dict[str, Room], room_id: str) -> None:
    """
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

    Short-circuits immediately on the first deficient equipment item.

    Args:
        room (Room): The room to check.
        required (Dict[str, int]): Equipment name to minimum count.

    Returns:
        bool: True if every required item is present in enough numbers.
    """
    for item_name, minimum in required.items():
        if room.equipment.get(item_name, 0) < minimum:
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
    if isinstance(group_size, bool) or not isinstance(group_size, int):
        raise InvalidRoomError("Group size must be a whole number.")
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

    Evaluates fast O(1) integer capacity checks first before inspecting
    equipment dictionaries or iterating closure dates.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        group_size (int): Number of students that must fit.
        start_date (date): First day the room is needed.
        end_date (date): Last day the room is needed (inclusive).
        required_equipment (Optional[Dict[str, int]]): Minimum equipment.

    Returns:
        Iterator[Room]: Matching rooms in insertion order.
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
    Uses min() with a generator to avoid the O(n log n) sorting cost
    and maintain O(1) auxiliary space. Ties are broken deterministically
    by room id.

    Args:
        rooms (Dict[str, Room]): Room data keyed by room id.
        group_size (int): Number of students that must fit.
        start_date (date): First day the room is needed.
        end_date (date): Last day the room is needed (inclusive).
        required_equipment (Optional[Dict[str, int]]): Minimum equipment.

    Returns:
        Optional[Room]: Smallest fitting room, or None if no match.

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
