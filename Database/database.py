# file: database.py
# purpose: SQLite persistence layer for Room Data, User Data, and sessions
# author: Thiri Htet Thwe (Thiri)
# Owner: Micky (rooms), Thiri (users, sessions), Jan (reservations)
# date: 2026-10-20

from datetime import date, datetime, time
import json
from pathlib import Path
import sqlite3
import sys
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "RoomService"))
sys.path.insert(0, str(BASE_DIR / "AuthService"))
sys.path.insert(0, str(BASE_DIR / "Reservation"))

from auth_service import Session, User  # noqa: E402
from reservation_data import Repetition, Reservation  # noqa: E402
from room_service import Room, UnavailablePeriod  # noqa: E402

DEFAULT_DB_FILE = "app.db"


def get_connection(db_path: str = DEFAULT_DB_FILE) -> sqlite3.Connection:
    """
    Open an SQLite database connection with row factory and foreign keys.

    Args:
        db_path (str): Filepath to the database or ':memory:'.

    Returns:
        sqlite3.Connection: Configured SQLite database connection.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """
    Create database tables for rooms, closures, users, and sessions.

    Args:
        conn (sqlite3.Connection): Database connection.

    Returns:
        None
    """
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                capacity INTEGER NOT NULL,
                equipment_json TEXT NOT NULL DEFAULT '{}'
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS unavailable_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                    ON DELETE CASCADE
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT ''
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                competency TEXT NOT NULL,
                room_id TEXT NOT NULL,
                group_size INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                repetition TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                    ON DELETE CASCADE
            );
        """)


# Room Persistence Functions
def save_room(conn: sqlite3.Connection, room: Room) -> None:
    """
    Insert or update a room record in SQLite.

    Args:
        conn (sqlite3.Connection): Database connection.
        room (Room): Room instance to persist.

    Returns:
        None
    """
    eq_json = json.dumps(room.equipment)
    with conn:
        conn.execute(
            """
            INSERT INTO rooms (room_id, name, capacity, equipment_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id) DO UPDATE SET
                name = excluded.name,
                capacity = excluded.capacity,
                equipment_json = excluded.equipment_json;
            """,
            (room.room_id, room.name, room.capacity, eq_json),
        )


def delete_room(conn: sqlite3.Connection, room_id: str) -> None:
    """
    Delete a room record and its closure periods from SQLite.

    Args:
        conn (sqlite3.Connection): Database connection.
        room_id (str): Identifier of the room to delete.

    Returns:
        None
    """
    with conn:
        conn.execute("DELETE FROM rooms WHERE room_id = ?;", (room_id,))


def save_unavailable_period(
    conn: sqlite3.Connection, room_id: str, period: UnavailablePeriod
) -> None:
    """
    Save an unavailable period associated with a room.

    Args:
        conn (sqlite3.Connection): Database connection.
        room_id (str): Associated room ID.
        period (UnavailablePeriod): Period to save.

    Returns:
        None
    """
    with conn:
        conn.execute(
            """
            INSERT INTO unavailable_periods
            (room_id, start_date, end_date, reason)
            VALUES (?, ?, ?, ?);
            """,
            (
                room_id,
                period.start_date.isoformat(),
                period.end_date.isoformat(),
                period.reason,
            ),
        )


def load_rooms(conn: sqlite3.Connection) -> Dict[str, Room]:
    """
    Load all rooms and their unavailable periods from SQLite into memory.

    Args:
        conn (sqlite3.Connection): Database connection.

    Returns:
        Dict[str, Room]: Dictionary of Room instances keyed by room_id.
    """
    rooms: Dict[str, Room] = {}
    rows = conn.execute(
        "SELECT room_id, name, capacity, equipment_json FROM rooms;"
    ).fetchall()
    for row in rows:
        equipment = json.loads(row["equipment_json"])
        room = Room(
            room_id=row["room_id"],
            name=row["name"],
            capacity=row["capacity"],
            equipment=equipment,
        )
        rooms[room.room_id] = room

    period_rows = conn.execute(
        """
        SELECT room_id, start_date, end_date, reason
        FROM unavailable_periods;
        """
    ).fetchall()
    for prow in period_rows:
        rid = prow["room_id"]
        if rid in rooms:
            p = UnavailablePeriod(
                start_date=date.fromisoformat(prow["start_date"]),
                end_date=date.fromisoformat(prow["end_date"]),
                reason=prow["reason"],
            )
            rooms[rid].unavailable_periods.append(p)

    return rooms


# -------------------------------------------------------------
# User & Session Persistence Functions
# -------------------------------------------------------------

def save_user(conn: sqlite3.Connection, user: User) -> None:
    """
    Insert or update a user record in SQLite.

    Args:
        conn (sqlite3.Connection): Database connection.
        user (User): User profile to persist.

    Returns:
        None
    """
    with conn:
        conn.execute(
            """
            INSERT INTO users
            (user_id, email, password_hash, salt, role, name)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email = excluded.email,
                password_hash = excluded.password_hash,
                salt = excluded.salt,
                role = excluded.role,
                name = excluded.name;
            """,
            (
                user.user_id,
                user.email,
                user.password_hash,
                user.salt,
                user.role,
                user.name,
            ),
        )


def load_users(conn: sqlite3.Connection) -> Dict[str, User]:
    """
    Load all registered user accounts from SQLite keyed by email.

    Args:
        conn (sqlite3.Connection): Database connection.

    Returns:
        Dict[str, User]: Dictionary of User instances keyed by email.
    """
    users: Dict[str, User] = {}
    rows = conn.execute(
        "SELECT user_id, email, password_hash, salt, role, name FROM users;"
    ).fetchall()
    for row in rows:
        user = User(
            user_id=row["user_id"],
            email=row["email"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            role=row["role"],
            name=row["name"],
        )
        users[user.email] = user
    return users


def save_session(conn: sqlite3.Connection, session: Session) -> None:
    """
    Save an active authentication session to SQLite.

    Args:
        conn (sqlite3.Connection): Database connection.
        session (Session): Active session to persist.

    Returns:
        None
    """
    with conn:
        conn.execute(
            """
            INSERT INTO sessions (token, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(token) DO UPDATE SET
                expires_at = excluded.expires_at;
            """,
            (
                session.token,
                session.user_id,
                session.expires_at.isoformat(),
                session.created_at.isoformat(),
            ),
        )


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    """
    Remove an authenticated session from SQLite upon logout.

    Args:
        conn (sqlite3.Connection): Database connection.
        token (str): Session token to delete.

    Returns:
        None
    """
    with conn:
        conn.execute("DELETE FROM sessions WHERE token = ?;", (token,))


def load_sessions(conn: sqlite3.Connection) -> Dict[str, Session]:
    """
    Load non-expired sessions from SQLite into memory.

    Args:
        conn (sqlite3.Connection): Database connection.

    Returns:
        Dict[str, Session]: Dictionary of active sessions keyed by token.
    """
    sessions: Dict[str, Session] = {}
    now_iso = datetime.utcnow().isoformat()
    # Clean up expired sessions automatically
    with conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?;", (now_iso,))

    rows = conn.execute(
        "SELECT token, user_id, expires_at, created_at FROM sessions;"
    ).fetchall()
    for row in rows:
        session = Session(
            token=row["token"],
            user_id=row["user_id"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        sessions[session.token] = session
    return sessions


# -------------------------------------------------------------
# Reservation Persistence Functions
# -------------------------------------------------------------

def save_reservation(
    conn: sqlite3.Connection, reservation: Reservation
) -> None:
    """
    Insert or update a reservation record in SQLite.

    Args:
        conn (sqlite3.Connection): Database connection.
        reservation (Reservation): Reservation instance to persist.

    Returns:
        None
    """
    if reservation.reservation_id is None:
        raise ValueError("Cannot persist reservation without reservation_id.")

    end_d_str = (
        reservation.end_date.isoformat() if reservation.end_date else None
    )
    with conn:
        conn.execute(
            """
            INSERT INTO reservations
            (reservation_id, competency, room_id, group_size,
             start_date, end_date, start_time, end_time, repetition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(reservation_id) DO UPDATE SET
                competency = excluded.competency,
                room_id = excluded.room_id,
                group_size = excluded.group_size,
                start_date = excluded.start_date,
                end_date = excluded.end_date,
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                repetition = excluded.repetition;
            """,
            (
                reservation.reservation_id,
                reservation.competency,
                reservation.room_id,
                reservation.group_size,
                reservation.start_date.isoformat(),
                end_d_str,
                reservation.start_time.isoformat(),
                reservation.end_time.isoformat(),
                reservation.repetition.value,
            ),
        )


def delete_reservation(conn: sqlite3.Connection, reservation_id: str) -> None:
    """
    Delete a reservation record from SQLite by ID.

    Args:
        conn (sqlite3.Connection): Database connection.
        reservation_id (str): Identifier of the reservation.

    Returns:
        None
    """
    with conn:
        conn.execute(
            "DELETE FROM reservations WHERE reservation_id = ?;",
            (reservation_id,),
        )


def load_reservations(conn: sqlite3.Connection) -> Dict[str, Reservation]:
    """
    Load all reservation records from SQLite into memory.

    Args:
        conn (sqlite3.Connection): Database connection.

    Returns:
        Dict[str, Reservation]: Keyed by reservation_id.
    """
    reservations: Dict[str, Reservation] = {}
    rows = conn.execute(
        """
        SELECT reservation_id, competency, room_id, group_size,
               start_date, end_date, start_time, end_time, repetition
        FROM reservations;
        """
    ).fetchall()
    for row in rows:
        end_d = (
            date.fromisoformat(row["end_date"]) if row["end_date"] else None
        )
        res = Reservation(
            reservation_id=row["reservation_id"],
            competency=row["competency"],
            room_id=row["room_id"],
            group_size=row["group_size"],
            start_date=date.fromisoformat(row["start_date"]),
            end_date=end_d,
            start_time=time.fromisoformat(row["start_time"]),
            end_time=time.fromisoformat(row["end_time"]),
            repetition=Repetition(row["repetition"]),
        )
        reservations[res.reservation_id] = res
    return reservations
