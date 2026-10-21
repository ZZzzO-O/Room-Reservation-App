# file: seed_rooms.py
# purpose: Pre-populate official CMKL University classroom data
# author: Su Pyae Pyae Aung (Micky)
# date: 2026-10-20
"""Pre-populate official CMKL University classroom data."""

from typing import Dict

from room_service import Room, create_room


def load_cmkl_rooms(rooms: Dict[str, Room]) -> Dict[str, Room]:
    """
    Populate the room store with official CMKL campus classrooms.

    Classroom names match the CMKL campus building directory.
    Note: Room 706 (Apex Supercomputer) is excluded as it is a server
    facility, not a student bookable classroom.

    Args:
        rooms (Dict[str, Room]): Destination room dictionary.

    Returns:
        Dict[str, Room]: Populated room dictionary.
    """
    cmkl_catalog = [
        ("601", "Pioneer", 40, {"projector": 1, "whiteboard": 2}),
        ("602", "Voyager", 35, {"projector": 1, "whiteboard": 1}),
        ("603", "Cube", 30, {"projector": 1, "whiteboard": 1}),
        ("604", "Victor", 45, {"projector": 1, "mic": 1, "whiteboard": 2}),
        ("605", "Hero", 40, {"projector": 1, "whiteboard": 2}),
        ("606", "Console", 16, {"tv_screen": 1, "whiteboard": 1}),
        ("607", "Sandbox", 50, {"projector": 2, "mic": 2, "whiteboard": 2}),
        ("608", "Bridge", 60, {"projector": 2, "mic": 2, "whiteboard": 2}),
        ("609", "Odyssey", 45, {"projector": 1, "whiteboard": 2}),
        ("705", "Kernel", 35, {"projector": 1, "whiteboard": 1}),
    ]

    for room_id, name, capacity, equipment in cmkl_catalog:
        create_room(
            rooms=rooms,
            room_id=room_id,
            capacity=capacity,
            equipment=equipment,
            name=name,
        )

    return rooms
