# pylint: disable=invalid-name,wildcard-import,unused-wildcard-import
"""
Database package providing SQLite persistence for rooms, users, and bookings.
"""

try:
    from .database import (  # noqa: F401
        DEFAULT_DB_FILE,
        delete_reservation,
        delete_room,
        delete_session,
        delete_unavailable_period,
        get_connection,
        init_db,
        load_reservations,
        load_rooms,
        load_sessions,
        load_users,
        save_reservation,
        save_room,
        save_session,
        save_unavailable_period,
        update_unavailable_period,
        save_user,
    )
except ImportError:
    pass
