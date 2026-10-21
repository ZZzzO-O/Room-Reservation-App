# pylint: disable=invalid-name
"""
Database package for Classroom Reservation Application (Team Vibranium).
Provides SQLite permanent persistence layer for rooms, users, and reservations.
"""

from .database import (
    DEFAULT_DB_FILE,
    get_connection,
    init_db,
    save_room,
    load_rooms,
    delete_room,
    save_unavailable_period,
    save_user,
    load_users,
    save_session,
    load_sessions,
    delete_session,
    save_reservation,
    load_reservations,
    delete_reservation,
)

__all__ = [
    "DEFAULT_DB_FILE",
    "get_connection",
    "init_db",
    "save_room",
    "load_rooms",
    "delete_room",
    "save_unavailable_period",
    "save_user",
    "load_users",
    "save_session",
    "load_sessions",
    "delete_session",
    "save_reservation",
    "load_reservations",
    "delete_reservation",
]
