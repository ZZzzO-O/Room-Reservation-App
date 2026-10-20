# file: test_api_gateway.py
# purpose: End-to-end integration tests for API Gateway and Network Service
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

import json
from pathlib import Path
import sys
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


if __name__ == "__main__":
    unittest.main()
