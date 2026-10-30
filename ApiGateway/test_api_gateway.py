# file: test_api_gateway.py
# purpose: End-to-end integration tests for API Gateway and Network Service
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20
"""Integration and end-to-end tests for API Gateway and service routing."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "ApiGateway"))

# pylint: disable=wrong-import-position
from api_gateway import create_app  # noqa: E402
# pylint: enable=wrong-import-position

STAFF = ("staff1@cmkl.ac.th", "Test@1234")
PROFESSOR = ("prof1@cmkl.ac.th", "Test@1234")
RESERVATION = {
    "competency": "SEN-201",
    "room_id": "601",
    "group_size": 30,
    "start_date": "2026-08-17",
    "end_date": "2026-12-01",
    "start_time": "10:00",
    "end_time": "12:00",
    "repetition": "Weekly",
}


def login(client, account: tuple) -> dict:
    """
    Log in and return the Authorization header for later requests.

    Args:
        client: Flask test client.
        account (tuple): (email, password).

    Returns:
        dict: {"Authorization": "Bearer <token>"}.
    """
    res = client.post(
        "/api/auth/login", json={"email": account[0], "password": account[1]}
    )
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


class GatewayTestCase(unittest.TestCase):
    """Fresh app with a throwaway in-memory database for every test."""

    def setUp(self) -> None:
        """Start the app and log in as Staff and Professor."""
        self.app = create_app(":memory:")
        self.client = self.app.test_client()
        self.staff = login(self.client, STAFF)
        self.prof = login(self.client, PROFESSOR)

    def book(self, **changes) -> object:
        """
        Create a reservation, overriding any RESERVATION fields given.

        Returns:
            The test client's response.
        """
        return self.client.post(
            "/api/reservations",
            json={**RESERVATION, **changes},
            headers=self.staff,
        )


class TestAuthRoutes(GatewayTestCase):
    """Test plan objective 1: log in and access control."""

    def test_root_lists_endpoints(self) -> None:
        """GET / reports the server is online."""
        data = self.client.get("/").get_json()
        self.assertEqual(data["status"], "online")
        self.assertIn("POST /api/auth/login", data["endpoints"])

    def test_1_1_login_returns_token_and_user(self) -> None:
        """1.1: Correct login returns a token and the user."""
        res = self.client.post(
            "/api/auth/login",
            json={"email": STAFF[0], "password": STAFF[1]},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["user"]["role"], "Staff")
        self.assertNotIn("password_hash", res.get_json()["user"])

    def test_1_2_and_1_3_bad_login_returns_401(self) -> None:
        """1.2 / 1.3: Unknown email and wrong password both give 401."""
        for email, password in (
            ("guest@gmail.com", "Test@1234"),
            (STAFF[0], "Wrong123"),
        ):
            res = self.client.post(
                "/api/auth/login", json={"email": email, "password": password}
            )
            self.assertEqual(res.status_code, 401)
            self.assertEqual(
                res.get_json()["error"], "Incorrect email or password."
            )

    def test_1_4_no_token_returns_401(self) -> None:
        """1.4: Calling the API without a token gives 401 and no data."""
        for headers in ({}, {"Authorization": "Bearer made-up"}):
            res = self.client.get("/api/rooms", headers=headers)
            self.assertEqual(res.status_code, 401)
            self.assertNotIn("rooms", res.get_json())

    def test_1_5_token_rejected_after_logout(self) -> None:
        """1.5: After logout the old token gives 401."""
        self.client.post("/api/auth/logout", headers=self.staff)
        res = self.client.get("/api/rooms", headers=self.staff)
        self.assertEqual(res.status_code, 401)

    def test_me_has_same_shape_as_login(self) -> None:
        """GET /api/auth/me returns {"user": {...}} like the login reply."""
        res = self.client.get("/api/auth/me", headers=self.staff)
        self.assertEqual(res.get_json()["user"]["email"], STAFF[0])


class TestRoomRoutes(GatewayTestCase):
    """Rooms: CRUD, Staff-only rules, search."""

    def test_staff_creates_room(self) -> None:
        """Staff can add a room."""
        res = self.client.post(
            "/api/rooms",
            json={"room_id": "999", "capacity": 50, "name": "Test"},
            headers=self.staff,
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["room"]["capacity"], 50)

    def test_professor_cannot_change_rooms(self) -> None:
        """Professors get 403 on Staff-only routes."""
        res = self.client.post(
            "/api/rooms",
            json={"room_id": "999", "capacity": 50},
            headers=self.prof,
        )
        self.assertEqual(res.status_code, 403)

    def test_room_errors(self) -> None:
        """Duplicate id 409, bad capacity 400, unknown room 404."""
        cases = [
            ("post", "/api/rooms", {"room_id": "601", "capacity": 30}, 409),
            ("post", "/api/rooms", {"room_id": "998", "capacity": 0}, 400),
            ("get", "/api/rooms/nope", None, 404),
            ("delete", "/api/rooms/nope", None, 404),
        ]
        for method, url, payload, status in cases:
            with self.subTest(method=method, url=url):
                res = getattr(self.client, method)(
                    url, json=payload, headers=self.staff
                )
                self.assertEqual(res.status_code, status)
                self.assertIn("error", res.get_json())

    def test_edit_and_delete_room(self) -> None:
        """Staff can edit, then delete, a room."""
        res = self.client.put(
            "/api/rooms/606", json={"capacity": 20}, headers=self.staff
        )
        self.assertEqual(res.get_json()["room"]["capacity"], 20)
        res = self.client.delete("/api/rooms/606", headers=self.staff)
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/api/rooms/606", headers=self.staff)
        self.assertEqual(res.status_code, 404)

    def test_mark_unavailable(self) -> None:
        """Closing a room works; a bad date gives a clear 400."""
        url = "/api/rooms/601/unavailable"
        res = self.client.post(url, headers=self.staff, json={
            "start_date": "2026-10-19",
            "end_date": "2026-10-30",
            "reason": "Renovation",
        })
        self.assertEqual(res.status_code, 201)
        res = self.client.post(url, headers=self.staff, json={
            "start_date": "19/10/2026", "end_date": "2026-10-30",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("YYYY-MM-DD", res.get_json()["error"])

    def test_mark_unavailable_rejects_existing_booking(self) -> None:
        """An overlapping booking blocks closure and remains intact."""
        booking = self.book(
            room_id="601",
            start_date="2026-11-05",
            end_date=None,
            repetition="Once",
        )
        self.assertEqual(booking.status_code, 201)
        reservation_id = booking.get_json()["reservation"]["reservation_id"]

        closure = self.client.post(
            "/api/rooms/601/unavailable",
            headers=self.staff,
            json={
                "start_date": "2026-11-04",
                "end_date": "2026-11-10",
                "reason": "Renovation",
            },
        )

        self.assertEqual(closure.status_code, 409)
        self.assertEqual(closure.get_json()["conflict_date"], "2026-11-05")
        self.assertEqual(
            closure.get_json()["conflicting_reservation"]["reservation_id"],
            reservation_id,
        )
        reservations = self.client.get(
            "/api/reservations?room_id=601", headers=self.staff
        ).get_json()["reservations"]
        self.assertEqual(
            [reservation["reservation_id"] for reservation in reservations],
            [reservation_id],
        )
        room = self.client.get(
            "/api/rooms/601", headers=self.staff
        ).get_json()["room"]
        self.assertEqual(room["unavailable_periods"], [])

    def test_available_and_recommend(self) -> None:
        """Search only returns rooms that fit; recommend picks smallest."""
        query = "?group_size=55&start_date=2026-10-14&end_date=2026-10-14"
        res = self.client.get("/api/rooms/available" + query,
                              headers=self.staff)
        ids = [room["room_id"] for room in res.get_json()["rooms"]]
        self.assertEqual(ids, ["608"])
        res = self.client.get("/api/rooms/recommend" + query,
                              headers=self.staff)
        self.assertEqual(res.get_json()["recommended_room"]["room_id"], "608")


class TestReservationRoutes(GatewayTestCase):
    """Reservations: create, conflicts, edit, delete, schedule."""

    def test_create_reservation(self) -> None:
        """A valid booking returns 201 and an id."""
        res = self.book()
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.get_json()["reservation"]["reservation_id"])

    def test_create_errors(self) -> None:
        """Conflict 409, too big 400, unknown room 404, missing time 400."""
        self.book()
        res = self.book(start_time="11:00", end_time="13:00")
        self.assertEqual(res.status_code, 409)
        self.assertIn("conflicting_reservation", res.get_json())
        self.assertEqual(self.book(group_size=500).status_code, 400)
        self.assertEqual(self.book(room_id="nope").status_code, 404)
        res = self.book(start_time="")
        self.assertEqual(res.status_code, 400)
        self.assertIn("start_time is required", res.get_json()["error"])

    def test_back_to_back_is_allowed(self) -> None:
        """A slot starting when another ends is not a conflict."""
        self.book()
        res = self.book(start_time="12:00", end_time="14:00")
        self.assertEqual(res.status_code, 201)

    def test_edit_keeps_unchanged_fields(self) -> None:
        """Editing one field keeps the others."""
        res_id = self.book().get_json()["reservation"]["reservation_id"]
        res = self.client.put(
            f"/api/reservations/{res_id}",
            json={"group_size": 25},
            headers=self.staff,
        )
        data = res.get_json()["reservation"]
        self.assertEqual(data["group_size"], 25)
        self.assertEqual(data["competency"], "SEN-201")

    def test_delete_then_not_found(self) -> None:
        """After delete, the reservation gives 404."""
        res_id = self.book().get_json()["reservation"]["reservation_id"]
        url = f"/api/reservations/{res_id}"
        self.assertEqual(
            self.client.delete(url, headers=self.staff).status_code, 200
        )
        for method in ("get", "put", "delete"):
            res = getattr(self.client, method)(url, headers=self.staff)
            self.assertEqual(res.status_code, 404)

    def test_search_schedule_and_export(self) -> None:
        """Search, weekly schedule, and text export all find the booking."""
        self.book()
        res = self.client.get(
            "/api/reservations/search?competency=SEN", headers=self.staff
        )
        self.assertEqual(res.get_json()["total"], 1)
        week = "?week_start=2026-08-17"
        res = self.client.get(
            "/api/reservations/schedule" + week, headers=self.staff
        )
        self.assertEqual(res.get_json()["total"], 1)
        res = self.client.get(
            "/api/reservations/export" + week, headers=self.staff
        )
        self.assertIn("SEN-201", res.get_data(as_text=True))
        res = self.client.get(
            "/api/reservations/schedule", headers=self.staff
        )
        self.assertEqual(res.status_code, 400)


class TestPersistence(unittest.TestCase):
    """Test plan 9.1: data survives a server restart."""

    def test_data_survives_restart(self) -> None:
        """Room, reservation, and login session are reloaded from SQLite."""
        fd, db_file = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            first = create_app(db_file)
            client = first.test_client()
            staff = login(client, STAFF)
            client.post("/api/rooms", headers=staff,
                        json={"room_id": "901", "capacity": 75})
            res = client.post("/api/reservations", headers=staff,
                              json={**RESERVATION, "room_id": "901"})
            res_id = res.get_json()["reservation"]["reservation_id"]

            second = create_app(db_file)
            restarted = second.test_client()
            res = restarted.get("/api/rooms/901", headers=staff)
            self.assertEqual(res.status_code, 200)
            res = restarted.get(f"/api/reservations/{res_id}", headers=staff)
            self.assertEqual(res.get_json()["reservation"]["room_id"], "901")
            first.config["STATE"].conn.close()
            second.config["STATE"].conn.close()
        finally:
            os.remove(db_file)


if __name__ == "__main__":
    unittest.main()
