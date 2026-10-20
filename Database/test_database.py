# file: test_database.py
# purpose: Unit tests for SQLite database persistence layer
# author: Su Pyae Pyae Aung (Micky) & Thiri Htet Thwe (Thiri)
# date: 2026-10-20

from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "RoomService"))
sys.path.insert(0, str(BASE_DIR / "AuthService"))
sys.path.insert(0, str(BASE_DIR / "Reservation"))
sys.path.insert(0, str(BASE_DIR / "Database"))

import auth_service as auth  # noqa: E402
from auth_service import Session, User  # noqa: E402
import database as db  # noqa: E402
from reservation_data import Repetition, Reservation  # noqa: E402
from room_service import Room, UnavailablePeriod  # noqa: E402


class DatabaseTestCase(unittest.TestCase):
    """Base test case initializing an in-memory SQLite database."""

    def setUp(self) -> None:
        """Initialize in-memory SQLite database with active schema."""
        self.conn = db.get_connection(":memory:")
        db.init_db(self.conn)

    def tearDown(self) -> None:
        """Close database connection."""
        self.conn.close()


class TestRoomPersistence(DatabaseTestCase):
    """Test suite covering room and closure persistence in SQLite."""

    def test_save_and_load_room(self) -> None:
        """Save room to SQLite and verify round-trip deserialization."""
        room = Room(
            room_id="601",
            name="Pioneer",
            capacity=40,
            equipment={"projector": 1, "whiteboard": 2},
        )
        db.save_room(self.conn, room)
        loaded = db.load_rooms(self.conn)

        self.assertIn("601", loaded)
        self.assertEqual(loaded["601"].name, "Pioneer")
        self.assertEqual(loaded["601"].capacity, 40)
        self.assertEqual(loaded["601"].equipment["projector"], 1)

    def test_update_existing_room(self) -> None:
        """Update existing room capacity in SQLite."""
        room = Room("601", 40, name="Pioneer")
        db.save_room(self.conn, room)

        room.capacity = 50
        room.name = "Pioneer Grand"
        db.save_room(self.conn, room)

        loaded = db.load_rooms(self.conn)
        self.assertEqual(loaded["601"].capacity, 50)
        self.assertEqual(loaded["601"].name, "Pioneer Grand")

    def test_delete_room_removes_from_sqlite(self) -> None:
        """Delete room removes record from SQLite database."""
        room = Room("601", 40)
        db.save_room(self.conn, room)
        db.delete_room(self.conn, "601")

        loaded = db.load_rooms(self.conn)
        self.assertNotIn("601", loaded)

    def test_save_and_load_unavailable_period(self) -> None:
        """Save unavailable period and verify link to parent room."""
        room = Room("601", 40, name="Pioneer")
        db.save_room(self.conn, room)

        period = UnavailablePeriod(
            start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 6),
            reason="Renovation",
        )
        db.save_unavailable_period(self.conn, "601", period)

        loaded = db.load_rooms(self.conn)
        self.assertEqual(len(loaded["601"].unavailable_periods), 1)
        p = loaded["601"].unavailable_periods[0]
        self.assertEqual(p.start_date, date(2026, 11, 2))
        self.assertEqual(p.end_date, date(2026, 11, 6))
        self.assertEqual(p.reason, "Renovation")


class TestUserAndSessionPersistence(DatabaseTestCase):
    """Test suite covering user profiles and session persistence."""

    def test_save_and_load_user(self) -> None:
        """Save user profile to SQLite and reload by email."""
        user = User(
            user_id="USR-100",
            email="staff1@cmkl.ac.th",
            password_hash="hash123",
            salt="salt123",
            role=auth.ROLE_STAFF,
            name="Staff One",
        )
        db.save_user(self.conn, user)
        loaded = db.load_users(self.conn)

        self.assertIn("staff1@cmkl.ac.th", loaded)
        self.assertEqual(loaded["staff1@cmkl.ac.th"].role, auth.ROLE_STAFF)
        self.assertEqual(loaded["staff1@cmkl.ac.th"].user_id, "USR-100")

    def test_save_and_load_session(self) -> None:
        """Save active session and reload active tokens."""
        user = User(
            "USR-100",
            "staff1@cmkl.ac.th",
            "hash123",
            "salt123",
            auth.ROLE_STAFF,
        )
        db.save_user(self.conn, user)

        session = Session(
            token="token-abc",
            user_id="USR-100",
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.save_session(self.conn, session)

        loaded = db.load_sessions(self.conn)
        self.assertIn("token-abc", loaded)
        self.assertEqual(loaded["token-abc"].user_id, "USR-100")

    def test_expired_session_is_purged_on_load(self) -> None:
        """Expired sessions are automatically purged when loading."""
        user = User(
            "USR-100",
            "staff1@cmkl.ac.th",
            "hash123",
            "salt123",
            auth.ROLE_STAFF,
        )
        db.save_user(self.conn, user)

        expired_session = Session(
            token="token-expired",
            user_id="USR-100",
            expires_at=datetime.utcnow() - timedelta(minutes=10),
        )
        db.save_session(self.conn, expired_session)

        loaded = db.load_sessions(self.conn)
        self.assertNotIn("token-expired", loaded)

    def test_delete_session(self) -> None:
        """Revoked session token is deleted from SQLite."""
        user = User(
            "USR-100",
            "staff1@cmkl.ac.th",
            "hash123",
            "salt123",
            auth.ROLE_STAFF,
        )
        db.save_user(self.conn, user)

        session = Session(
            token="token-logout",
            user_id="USR-100",
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.save_session(self.conn, session)
        db.delete_session(self.conn, "token-logout")

        loaded = db.load_sessions(self.conn)
        self.assertNotIn("token-logout", loaded)


class TestReservationPersistence(DatabaseTestCase):
    """Test suite covering reservation persistence in SQLite."""

    def setUp(self) -> None:
        """Set up in-memory DB and seed parent room."""
        super().setUp()
        room = Room(room_id="601", capacity=40, name="Pioneer")
        db.save_room(self.conn, room)

    def test_save_and_load_reservation(self) -> None:
        """Save weekly reservation and reload from SQLite."""
        res = Reservation(
            reservation_id="RES-001",
            competency="SEN-201",
            room_id="601",
            group_size=30,
            start_date=date(2026, 8, 17),
            end_date=date(2026, 12, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            repetition=Repetition.WEEKLY,
        )
        db.save_reservation(self.conn, res)
        loaded = db.load_reservations(self.conn)

        self.assertIn("RES-001", loaded)
        loaded_res = loaded["RES-001"]
        self.assertEqual(loaded_res.competency, "SEN-201")
        self.assertEqual(loaded_res.room_id, "601")
        self.assertEqual(loaded_res.group_size, 30)
        self.assertEqual(loaded_res.start_date, date(2026, 8, 17))
        self.assertEqual(loaded_res.end_date, date(2026, 12, 1))
        self.assertEqual(loaded_res.start_time, time(10, 0))
        self.assertEqual(loaded_res.end_time, time(12, 0))
        self.assertEqual(loaded_res.repetition, Repetition.WEEKLY)

    def test_update_reservation(self) -> None:
        """Update existing reservation fields in SQLite."""
        res = Reservation(
            reservation_id="RES-001",
            competency="SEN-201",
            room_id="601",
            group_size=30,
            start_date=date(2026, 8, 17),
            start_time=time(10, 0),
            end_time=time(12, 0),
            repetition=Repetition.ONCE,
        )
        db.save_reservation(self.conn, res)

        res.group_size = 35
        res.competency = "SEN-201 Advanced"
        db.save_reservation(self.conn, res)

        loaded = db.load_reservations(self.conn)
        self.assertEqual(loaded["RES-001"].group_size, 35)
        self.assertEqual(loaded["RES-001"].competency, "SEN-201 Advanced")

    def test_delete_reservation(self) -> None:
        """Delete reservation removes record from SQLite."""
        res = Reservation(
            reservation_id="RES-001",
            competency="SEN-201",
            room_id="601",
            group_size=30,
            start_date=date(2026, 8, 17),
            start_time=time(10, 0),
            end_time=time(12, 0),
        )
        db.save_reservation(self.conn, res)
        db.delete_reservation(self.conn, "RES-001")

        loaded = db.load_reservations(self.conn)
        self.assertNotIn("RES-001", loaded)


if __name__ == "__main__":
    unittest.main()
