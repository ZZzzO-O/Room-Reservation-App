# file: test_api_gateway.py
# purpose: End-to-end integration tests for API Gateway and Network Service
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "RoomService"))
sys.path.insert(0, str(BASE_DIR / "AuthService"))
sys.path.insert(0, str(BASE_DIR / "ApiGateway"))

from api_gateway import create_app  # noqa: E402
import auth_service as auth  # noqa: E402


class ApiGatewayTestCase(unittest.TestCase):
    """Base test case initializing Flask test client with seeded stores."""

    def setUp(self) -> None:
        """Configure test client with fresh isolated data stores."""
        self.users = {}
        self.sessions = {}
        self.rooms = {}
        self.app = create_app(self.users, self.sessions, self.rooms)
        self.client = self.app.test_client()

        # Generate active tokens for Staff and Professor
        _, staff_session = auth.authenticate(
            self.users, self.sessions, "staff1@cmkl.ac.th", "Test@1234"
        )
        self.staff_token = staff_session.token

        _, prof_session = auth.authenticate(
            self.users, self.sessions, "prof1@cmkl.ac.th", "Test@1234"
        )
        self.prof_token = prof_session.token

    def staff_headers(self) -> dict:
        """Authorization header for Staff user."""
        return {"Authorization": f"Bearer {self.staff_token}"}

    def prof_headers(self) -> dict:
        """Authorization header for Professor user."""
        return {"Authorization": f"Bearer {self.prof_token}"}


class TestAuthEndpoints(ApiGatewayTestCase):
    """Test suite covering authentication API routes."""

    def test_root_endpoint_returns_directory(self) -> None:
        """GET / returns 200 with online status and endpoints."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "online")
        self.assertIn("endpoints", data)

    def test_login_valid_credentials(self) -> None:
        """POST /api/auth/login with valid data returns 200 and token."""
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "staff1@cmkl.ac.th",
                "password": "Test@1234",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], auth.ROLE_STAFF)

    def test_login_invalid_credentials_returns_401(self) -> None:
        """POST /api/auth/login with wrong password returns 401."""
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "staff1@cmkl.ac.th",
                "password": "WrongPassword",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("error", res.get_json())

    def test_get_me_authenticated(self) -> None:
        """GET /api/auth/me returns profile of logged-in user."""
        res = self.client.get("/api/auth/me", headers=self.staff_headers())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["email"], "staff1@cmkl.ac.th")

    def test_logout_terminates_session(self) -> None:
        """POST /api/auth/logout revokes session token."""
        res = self.client.post(
            "/api/auth/logout", headers=self.staff_headers()
        )
        self.assertEqual(res.status_code, 200)

        # Subsequent authenticated calls should fail with 401
        res_after = self.client.get(
            "/api/auth/me", headers=self.staff_headers()
        )
        self.assertEqual(res_after.status_code, 401)


class TestRoomEndpoints(ApiGatewayTestCase):
    """Test suite covering room CRUD and role enforcement."""

    def test_unauthenticated_request_rejected(self) -> None:
        """TC-1.4: Direct API call without token returns 401."""
        res = self.client.get("/api/rooms")
        self.assertEqual(res.status_code, 401)

    def test_staff_can_create_room(self) -> None:
        """Staff can create room via POST /api/rooms."""
        res = self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=json.dumps({
                "room_id": "601",
                "capacity": 40,
                "name": "Pioneer",
                "equipment": {"projector": 1},
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["room"]
        self.assertEqual(data["room_id"], "601")
        self.assertEqual(data["name"], "Pioneer")

    def test_professor_cannot_create_room(self) -> None:
        """Professor attempting to create room receives 403 Forbidden."""
        res = self.client.post(
            "/api/rooms",
            headers=self.prof_headers(),
            data=json.dumps({
                "room_id": "602",
                "capacity": 30,
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Forbidden", res.get_json()["error"])

    def test_duplicate_room_returns_409(self) -> None:
        """Attempting to create duplicate room ID returns 409 Conflict."""
        payload = json.dumps({"room_id": "601", "capacity": 40})
        self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=payload,
            content_type="application/json",
        )
        res = self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 409)

    def test_invalid_room_data_returns_400(self) -> None:
        """Invalid room capacity returns 400 Bad Request."""
        res = self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=json.dumps({"room_id": "601", "capacity": -5}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_get_single_room(self) -> None:
        """GET /api/rooms/<id> returns room details."""
        self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=json.dumps({"room_id": "601", "capacity": 40}),
            content_type="application/json",
        )
        res = self.client.get(
            "/api/rooms/601", headers=self.prof_headers()
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["room"]["room_id"], "601")

    def test_get_missing_room_returns_404(self) -> None:
        """GET /api/rooms/<id> for nonexistent room returns 404."""
        res = self.client.get(
            "/api/rooms/Z999", headers=self.staff_headers()
        )
        self.assertEqual(res.status_code, 404)

    def test_edit_room_as_staff(self) -> None:
        """Staff can update room capacity and equipment."""
        self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=json.dumps({"room_id": "601", "capacity": 40}),
            content_type="application/json",
        )
        res = self.client.put(
            "/api/rooms/601",
            headers=self.staff_headers(),
            data=json.dumps({"capacity": 55, "name": "Pioneer Updated"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["room"]["capacity"], 55)

    def test_delete_room_as_staff(self) -> None:
        """Staff can delete existing room."""
        self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=json.dumps({"room_id": "601", "capacity": 40}),
            content_type="application/json",
        )
        res = self.client.delete(
            "/api/rooms/601", headers=self.staff_headers()
        )
        self.assertEqual(res.status_code, 200)

    def test_mark_room_unavailable(self) -> None:
        """Staff can mark a room closed for renovation."""
        self.client.post(
            "/api/rooms",
            headers=self.staff_headers(),
            data=json.dumps({"room_id": "601", "capacity": 40}),
            content_type="application/json",
        )
        res = self.client.post(
            "/api/rooms/601/unavailable",
            headers=self.staff_headers(),
            data=json.dumps({
                "start_date": "2026-10-15",
                "end_date": "2026-10-20",
                "reason": "Renovation",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)


class TestSearchAndSeedEndpoints(ApiGatewayTestCase):
    """Test suite covering room filtering, recommendation, and seeding."""

    def setUp(self) -> None:
        """Seed rooms before testing search and recommendation."""
        super().setUp()
        self.client.post("/api/rooms/seed", headers=self.staff_headers())

    def test_seed_rooms_populates_cmkl(self) -> None:
        """POST /api/rooms/seed populates 10 CMKL classrooms."""
        res = self.client.get("/api/rooms", headers=self.prof_headers())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["total"], 10)

    def test_find_available_rooms(self) -> None:
        """GET /api/rooms/available filters rooms by group size and dates."""
        query = (
            "/api/rooms/available?group_size=40&start_date=2026-11-02&"
            "end_date=2026-11-06&projector=1"
        )
        res = self.client.get(query, headers=self.prof_headers())
        self.assertEqual(res.status_code, 200)
        rooms = res.get_json()["rooms"]
        self.assertTrue(all(r["capacity"] >= 40 for r in rooms))

    def test_recommend_room(self) -> None:
        """GET /api/rooms/recommend returns single tightest-fit room."""
        query = (
            "/api/rooms/recommend?group_size=35&start_date=2026-11-02&"
            "end_date=2026-11-06&projector=1"
        )
        res = self.client.get(query, headers=self.prof_headers())
        self.assertEqual(res.status_code, 200)
        rec = res.get_json()["recommended_room"]
        self.assertIsNotNone(rec)
        self.assertEqual(rec["capacity"], 35)


class TestSqlitePersistenceThroughGateway(unittest.TestCase):
    """Test suite verifying persistence across simulated server restarts."""

    def test_room_persists_across_app_recreation(self) -> None:
        """Create room in instance 1 and verify it reloads in instance 2."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db = tmp.name

        try:
            # Instance 1: Create room
            app1 = create_app(db_path=tmp_db)
            c1 = app1.test_client()

            login_res = c1.post(
                "/api/auth/login",
                data=json.dumps({
                    "email": "staff1@cmkl.ac.th",
                    "password": "Test@1234",
                }),
                content_type="application/json",
            )
            token = login_res.get_json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            create_res = c1.post(
                "/api/rooms",
                headers=headers,
                data=json.dumps({
                    "room_id": "901",
                    "capacity": 75,
                    "name": "SuperLab",
                }),
                content_type="application/json",
            )
            self.assertEqual(create_res.status_code, 201)

            # Instance 2: Simulate complete server reboot with new stores
            app2 = create_app(db_path=tmp_db)
            c2 = app2.test_client()

            get_res = c2.get("/api/rooms/901", headers=headers)
            self.assertEqual(get_res.status_code, 200)
            data = get_res.get_json()["room"]
            self.assertEqual(data["room_id"], "901")
            self.assertEqual(data["name"], "SuperLab")
            self.assertEqual(data["capacity"], 75)
        finally:
            if "app1" in locals() and getattr(app1, "conn", None):
                app1.conn.close()
            if "app2" in locals() and getattr(app2, "conn", None):
                app2.conn.close()
            if os.path.exists(tmp_db):
                os.remove(tmp_db)

    def test_reservation_persists_across_reboot(self) -> None:
        """Reservation saved in SQLite survives complete app reboot."""
        tmp_db = os.path.join(tempfile.gettempdir(), "test_res_persist.db")
        if os.path.exists(tmp_db):
            os.remove(tmp_db)

        try:
            app1 = create_app(db_path=tmp_db)
            c1 = app1.test_client()
            login_res = c1.post(
                "/api/auth/login",
                data=json.dumps({
                    "email": "staff1@cmkl.ac.th",
                    "password": "Test@1234",
                }),
                content_type="application/json",
            )
            token = login_res.get_json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            create_res = c1.post(
                "/api/reservations",
                headers=headers,
                data=json.dumps({
                    "competency": "SEN-201",
                    "room_id": "601",
                    "group_size": 30,
                    "start_date": "2026-08-17",
                    "end_date": "2026-12-01",
                    "start_time": "10:00",
                    "end_time": "12:00",
                    "repetition": "Weekly",
                }),
                content_type="application/json",
            )
            self.assertEqual(create_res.status_code, 201)
            res_id = create_res.get_json()["reservation"]["reservation_id"]

            # Reboot
            app2 = create_app(db_path=tmp_db)
            c2 = app2.test_client()

            get_res = c2.get(f"/api/reservations/{res_id}", headers=headers)
            self.assertEqual(get_res.status_code, 200)
            data = get_res.get_json()["reservation"]
            self.assertEqual(data["reservation_id"], res_id)
            self.assertEqual(data["competency"], "SEN-201")
        finally:
            if "app1" in locals() and getattr(app1, "conn", None):
                app1.conn.close()
            if "app2" in locals() and getattr(app2, "conn", None):
                app2.conn.close()
            if os.path.exists(tmp_db):
                os.remove(tmp_db)


class TestReservationEndpoints(ApiGatewayTestCase):
    """Test suite covering reservation creation, editing, and conflicts."""

    def setUp(self) -> None:
        """Configure test client and seed rooms."""
        super().setUp()
        self.client.post(
            "/api/rooms/seed", headers=self.staff_headers()
        )

    def test_create_reservation_success(self) -> None:
        """Create valid weekly reservation returns 201 Created."""
        res = self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps({
                "competency": "SEN-201",
                "room_id": "601",
                "group_size": 30,
                "start_date": "2026-08-17",
                "end_date": "2026-12-01",
                "start_time": "10:00",
                "end_time": "12:00",
                "repetition": "Weekly",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["reservation"]
        self.assertIsNotNone(data["reservation_id"])
        self.assertEqual(data["competency"], "SEN-201")
        self.assertEqual(data["day_of_week"], "Monday")

    def test_create_reservation_conflict_returns_409(self) -> None:
        """Attempting to double-book room returns 409 Conflict."""
        payload = {
            "competency": "SEN-201",
            "room_id": "601",
            "group_size": 30,
            "start_date": "2026-08-17",
            "end_date": "2026-12-01",
            "start_time": "10:00",
            "end_time": "12:00",
            "repetition": "Weekly",
        }
        res1 = self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res1.status_code, 201)

        # Overlapping time in same room
        payload["start_time"] = "11:00"
        payload["end_time"] = "13:00"
        payload["competency"] = "SEN-202"
        res2 = self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res2.status_code, 409)
        self.assertIn("conflicting_reservation", res2.get_json())

    def test_create_reservation_capacity_exceeded_returns_400(self) -> None:
        """Group size larger than room capacity returns 400 Bad Request."""
        res = self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps({
                "competency": "Large Class",
                "room_id": "601",
                "group_size": 999,
                "start_date": "2026-08-17",
                "start_time": "10:00",
                "end_time": "12:00",
                "repetition": "Once",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_create_reservation_unknown_room_returns_404(self) -> None:
        """Reserving a nonexistent room returns 404 Not Found."""
        res = self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps({
                "competency": "Ghost Class",
                "room_id": "ROOM-999",
                "group_size": 10,
                "start_date": "2026-08-17",
                "start_time": "10:00",
                "end_time": "12:00",
                "repetition": "Once",
            }),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 404)

    def test_list_and_search_reservations(self) -> None:
        """List and search endpoints return matching reservations."""
        for comp, room in [("Software Eng", "601"), ("AI Studio", "602")]:
            self.client.post(
                "/api/reservations",
                headers=self.staff_headers(),
                data=json.dumps({
                    "competency": comp,
                    "room_id": room,
                    "group_size": 20,
                    "start_date": "2026-08-17",
                    "start_time": "10:00",
                    "end_time": "12:00",
                    "repetition": "Once",
                }),
                content_type="application/json",
            )

        list_res = self.client.get(
            "/api/reservations", headers=self.staff_headers()
        )
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.get_json()["total"], 2)

        search_res = self.client.get(
            "/api/reservations/search?competency=Software",
            headers=self.staff_headers(),
        )
        self.assertEqual(search_res.status_code, 200)
        self.assertEqual(search_res.get_json()["total"], 1)

    def test_get_edit_and_delete_reservation(self) -> None:
        """Full lifecycle test: get, edit, and delete reservation."""
        create_res = self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps({
                "competency": "Networks",
                "room_id": "601",
                "group_size": 20,
                "start_date": "2026-08-17",
                "start_time": "10:00",
                "end_time": "12:00",
                "repetition": "Once",
            }),
            content_type="application/json",
        )
        res_id = create_res.get_json()["reservation"]["reservation_id"]

        get_res = self.client.get(
            f"/api/reservations/{res_id}", headers=self.staff_headers()
        )
        self.assertEqual(get_res.status_code, 200)

        edit_res = self.client.put(
            f"/api/reservations/{res_id}",
            headers=self.staff_headers(),
            data=json.dumps({"group_size": 25}),
            content_type="application/json",
        )
        self.assertEqual(edit_res.status_code, 200)
        self.assertEqual(
            edit_res.get_json()["reservation"]["group_size"], 25
        )

        del_res = self.client.delete(
            f"/api/reservations/{res_id}", headers=self.staff_headers()
        )
        self.assertEqual(del_res.status_code, 200)

        del_again = self.client.delete(
            f"/api/reservations/{res_id}", headers=self.staff_headers()
        )
        self.assertEqual(del_again.status_code, 404)

    def test_get_schedule_and_export(self) -> None:
        """Schedule and export return timetable and text file."""
        self.client.post(
            "/api/reservations",
            headers=self.staff_headers(),
            data=json.dumps({
                "competency": "Algorithms",
                "room_id": "601",
                "group_size": 25,
                "start_date": "2026-08-17",
                "end_date": "2026-12-01",
                "start_time": "10:00",
                "end_time": "12:00",
                "repetition": "Weekly",
            }),
            content_type="application/json",
        )

        sched_res = self.client.get(
            "/api/reservations/schedule?week_start=2026-08-17",
            headers=self.staff_headers(),
        )
        self.assertEqual(sched_res.status_code, 200)
        self.assertEqual(sched_res.get_json()["total"], 1)

        export_res = self.client.get(
            "/api/reservations/export?week_start=2026-08-17",
            headers=self.staff_headers(),
        )
        self.assertEqual(export_res.status_code, 200)
        self.assertIn("text/plain", export_res.content_type)
        self.assertIn(b"Algorithms", export_res.data)


if __name__ == "__main__":
    unittest.main()
