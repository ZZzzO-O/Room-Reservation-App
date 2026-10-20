# file: api_gateway.py
# purpose: REST API Gateway and Network Service routing for the web app
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

from datetime import date, time
from functools import wraps
from pathlib import Path
import sqlite3
import sys
from typing import Any, Callable, Dict, Optional, Tuple

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# Add sibling directories to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "RoomService"))
sys.path.insert(0, str(BASE_DIR / "AuthService"))
sys.path.insert(0, str(BASE_DIR / "Reservation"))
sys.path.insert(0, str(BASE_DIR / "Database"))

import auth_service as auth  # noqa: E402
import database as db  # noqa: E402
import reservation_data as rdata  # noqa: E402
import reservation_service as rservice  # noqa: E402
import room_service as rs  # noqa: E402
from seed_rooms import load_cmkl_rooms  # noqa: E402


def parse_date(date_str: str) -> date:
    """
    Parse an ISO date string (YYYY-MM-DD) into a date object.

    Args:
        date_str (str): Date string in YYYY-MM-DD format.

    Returns:
        date: Parsed date object.

    Raises:
        ValueError: If format is invalid.
    """
    return date.fromisoformat(date_str.strip())


def room_to_dict(room: rs.Room) -> Dict[str, Any]:
    """
    Serialize a Room dataclass instance into a JSON-compatible dictionary.

    Args:
        room (rs.Room): Room dataclass instance.

    Returns:
        Dict[str, Any]: Serialized dictionary representation.
    """
    return {
        "room_id": room.room_id,
        "name": room.name,
        "capacity": room.capacity,
        "equipment": room.equipment,
        "unavailable_periods": [
            {
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
                "reason": period.reason,
            }
            for period in room.unavailable_periods
        ],
    }


def parse_time(time_str: str) -> time:
    """
    Parse an ISO time string (HH:MM or HH:MM:SS) into a time object.

    Args:
        time_str (str): Time string.

    Returns:
        time: Parsed time object.

    Raises:
        ValueError: If format is invalid.
    """
    return time.fromisoformat(time_str.strip())


def reservation_to_dict(res: rdata.Reservation) -> Dict[str, Any]:
    """
    Serialize a Reservation dataclass into a JSON-compatible dictionary.

    Args:
        res (rdata.Reservation): Reservation dataclass instance.

    Returns:
        Dict[str, Any]: Serialized dictionary representation.
    """
    end_d_str = res.end_date.isoformat() if res.end_date else None
    return {
        "reservation_id": res.reservation_id,
        "competency": res.competency,
        "room_id": res.room_id,
        "group_size": res.group_size,
        "start_date": res.start_date.isoformat(),
        "end_date": end_d_str,
        "start_time": res.start_time.strftime("%H:%M"),
        "end_time": res.end_time.strftime("%H:%M"),
        "day_of_week": res.day_of_week.value,
        "repetition": res.repetition.value,
    }


class AppRoomCapacityProvider:
    """Adapter allowing ReservationService to query room capacities."""

    def __init__(self, rooms: Dict[str, rs.Room]) -> None:
        """
        Store reference to the rooms dictionary.

        Args:
            rooms (Dict[str, rs.Room]): Shared room dictionary.
        """
        self._rooms = rooms

    def get_room_capacity(self, room_id: str) -> Optional[int]:
        """
        Look up capacity for room_id.

        Args:
            room_id (str): Room identifier.

        Returns:
            Optional[int]: Capacity or None if not found.
        """
        room = self._rooms.get(room_id)
        return room.capacity if room is not None else None


def create_app(
    users: Optional[Dict[str, auth.User]] = None,
    sessions: Optional[Dict[str, auth.Session]] = None,
    rooms: Optional[Dict[str, rs.Room]] = None,
    reservations: Optional[rdata.ReservationRepository] = None,
    db_path: Optional[str] = None,
) -> Flask:
    """
    Application factory for the API Gateway and Network Service.

    Supports optional SQLite database persistence for long-term storage
    (retaining records across semesters / 4-year cycle).

    Args:
        users (Optional[Dict[str, auth.User]]): Pre-existing user store.
        sessions (Optional[Dict[str, auth.Session]]): Session store.
        rooms (Optional[Dict[str, rs.Room]]): Room data store.
        reservations (Optional[rdata.ReservationRepository]): Repository.
        db_path (Optional[str]): Path to SQLite database file or ':memory:'.

    Returns:
        Flask: Configured and route-registered Flask application.
    """
    app = Flask(__name__)
    CORS(app)

    # Initialize SQLite connection if db_path or default standalone startup
    conn: Optional[sqlite3.Connection] = None
    target_db = db_path
    if target_db is None and users is None and rooms is None:
        target_db = str(BASE_DIR / db.DEFAULT_DB_FILE)

    if target_db is not None:
        conn = db.get_connection(target_db)
        db.init_db(conn)

    app.conn = conn  # type: ignore[attr-defined]

    # Initialize shared stores
    app_users: Dict[str, auth.User] = {} if users is None else users
    app_sessions: Dict[str, auth.Session] = (
        {} if sessions is None else sessions
    )
    app_rooms: Dict[str, rs.Room] = {} if rooms is None else rooms
    app_res_repo: rdata.ReservationRepository = (
        rdata.ReservationRepository()
        if reservations is None
        else reservations
    )
    capacity_provider = AppRoomCapacityProvider(app_rooms)
    res_service = rservice.ReservationService(
        app_res_repo, capacity_provider
    )
    app.res_service = res_service  # type: ignore[attr-defined]
    app.res_repo = app_res_repo  # type: ignore[attr-defined]

    # Load from or populate SQLite
    if conn is not None:
        loaded_users = db.load_users(conn)
        if loaded_users:
            app_users.update(loaded_users)
        else:
            auth.seed_default_users(app_users)
            for u in app_users.values():
                db.save_user(conn, u)

        loaded_rooms = db.load_rooms(conn)
        if loaded_rooms:
            app_rooms.update(loaded_rooms)
        else:
            load_cmkl_rooms(app_rooms)
            for r in app_rooms.values():
                db.save_room(conn, r)

        loaded_reservations = db.load_reservations(conn)
        for res_obj in loaded_reservations.values():
            if app_res_repo.get_by_id(res_obj.reservation_id) is None:
                app_res_repo.add_reservation(res_obj)

        app_sessions.update(db.load_sessions(conn))
    else:
        if not app_users:
            auth.seed_default_users(app_users)
        if rooms is None:
            load_cmkl_rooms(app_rooms)

    def get_token_from_header() -> Optional[str]:
        """Extract Bearer token from the Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        return None

    def require_auth(func: Callable) -> Callable:
        """Decorator verifying that an incoming request is authenticated."""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Tuple[Response, int]:
            token = get_token_from_header()
            if not token:
                return jsonify({"error": "Authentication required."}), 401
            try:
                user = auth.validate_session(app_users, app_sessions, token)
            except auth.InvalidSessionError as err:
                return jsonify({"error": str(err)}), 401
            return func(user, *args, **kwargs)
        return wrapper

    def require_role(required_role: str) -> Callable:
        """Decorator restricting route access to a specific role."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(
                user: auth.User, *args: Any, **kwargs: Any
            ) -> Tuple[Response, int]:
                if user.role != required_role:
                    msg = (
                        f"Forbidden: {required_role} privileges required."
                    )
                    return jsonify({"error": msg}), 403
                return func(user, *args, **kwargs)
            return wrapper
        return decorator

    # ---------------------------------------------------------
    # Root & Diagnostic Route
    # ---------------------------------------------------------

    @app.route("/", methods=["GET"])
    def root() -> Tuple[Response, int]:
        """Root endpoint returning API status and endpoints directory."""
        storage_type = "SQLite (app.db)" if conn else "In-Memory"
        return jsonify({
            "name": "CMKL Classroom Reservation API Gateway",
            "version": "1.0.0",
            "status": "online",
            "team": "Vibranium",
            "storage": storage_type,
            "message": "API Gateway is running and ready for requests.",
            "endpoints": {
                "auth": [
                    "POST /api/auth/login",
                    "POST /api/auth/logout",
                    "GET /api/auth/me",
                ],
                "rooms": [
                    "GET /api/rooms",
                    "POST /api/rooms",
                    "GET /api/rooms/<id>",
                    "PUT /api/rooms/<id>",
                    "DELETE /api/rooms/<id>",
                    "POST /api/rooms/<id>/unavailable",
                    "GET /api/rooms/available",
                    "GET /api/rooms/recommend",
                    "POST /api/rooms/seed",
                ],
                "reservations": [
                    "GET /api/reservations",
                    "POST /api/reservations",
                    "GET /api/reservations/<id>",
                    "PUT /api/reservations/<id>",
                    "DELETE /api/reservations/<id>",
                    "GET /api/reservations/search",
                    "GET /api/reservations/schedule",
                    "GET /api/reservations/export",
                ],
            },
            "test_accounts": {
                "staff": "staff1@cmkl.ac.th (Password: Test@1234)",
                "professor": "prof1@cmkl.ac.th (Password: Test@1234)",
            },
        }), 200

    # ---------------------------------------------------------
    # Authentication Routes (OBJ-01)
    # ---------------------------------------------------------

    @app.route("/api/auth/login", methods=["POST"])
    def api_login() -> Tuple[Response, int]:
        """Authenticate user and return active session token."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        password = data.get("password", "")
        try:
            user, session = auth.authenticate(
                app_users, app_sessions, email, password
            )
            if conn is not None:
                db.save_session(conn, session)

            return jsonify({
                "token": session.token,
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "role": user.role,
                    "name": user.name,
                },
                "expires_at": session.expires_at.isoformat(),
            }), 200
        except auth.InvalidCredentialsError as err:
            return jsonify({"error": str(err)}), 401

    @app.route("/api/auth/logout", methods=["POST"])
    @require_auth
    def api_logout(user: auth.User) -> Tuple[Response, int]:
        """Revoke active session token."""
        token = get_token_from_header() or ""
        auth.terminate_session(app_sessions, token)
        if conn is not None:
            db.delete_session(conn, token)
        return jsonify({"message": "Logged out successfully."}), 200

    @app.route("/api/auth/me", methods=["GET"])
    @require_auth
    def api_me(user: auth.User) -> Tuple[Response, int]:
        """Return the profile of the currently logged-in user."""
        return jsonify({
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "name": user.name,
        }), 200

    # ---------------------------------------------------------
    # Room Management Routes (OBJ-02 & OBJ-03)
    # ---------------------------------------------------------

    @app.route("/api/rooms", methods=["GET"])
    @require_auth
    def list_rooms(user: auth.User) -> Tuple[Response, int]:
        """Retrieve all registered rooms."""
        room_list = [room_to_dict(r) for r in app_rooms.values()]
        return jsonify({"rooms": room_list, "total": len(room_list)}), 200

    @app.route("/api/rooms", methods=["POST"])
    @require_auth
    @require_role(auth.ROLE_STAFF)
    def api_create_room(user: auth.User) -> Tuple[Response, int]:
        """Create a new room (Staff only)."""
        data = request.get_json(silent=True) or {}
        room_id = data.get("room_id")
        capacity = data.get("capacity")
        equipment = data.get("equipment", {})
        name = data.get("name", "")

        try:
            room = rs.create_room(
                app_rooms,
                room_id=room_id,
                capacity=capacity,
                equipment=equipment,
                name=name,
            )
            if conn is not None:
                db.save_room(conn, room)

            return jsonify({
                "message": "Room created successfully.",
                "room": room_to_dict(room),
            }), 201
        except rs.DuplicateRoomError as err:
            return jsonify({"error": str(err)}), 409
        except rs.InvalidRoomError as err:
            return jsonify({"error": str(err)}), 400

    @app.route("/api/rooms/<room_id>", methods=["GET"])
    @require_auth
    def api_get_room(user: auth.User, room_id: str) -> Tuple[Response, int]:
        """Retrieve details of a single room."""
        try:
            room = rs.get_room(app_rooms, room_id)
            return jsonify({"room": room_to_dict(room)}), 200
        except rs.RoomNotFoundError as err:
            return jsonify({"error": str(err)}), 404

    @app.route("/api/rooms/<room_id>", methods=["PUT"])
    @require_auth
    @require_role(auth.ROLE_STAFF)
    def api_edit_room(user: auth.User, room_id: str) -> Tuple[Response, int]:
        """Update an existing room (Staff only)."""
        data = request.get_json(silent=True) or {}
        capacity = data.get("capacity")
        equipment = data.get("equipment")
        name = data.get("name")
        try:
            room = rs.edit_room(
                app_rooms,
                room_id=room_id,
                capacity=capacity,
                equipment=equipment,
                name=name,
            )
            if conn is not None:
                db.save_room(conn, room)

            return jsonify({
                "message": "Room updated successfully.",
                "room": room_to_dict(room),
            }), 200
        except rs.RoomNotFoundError as err:
            return jsonify({"error": str(err)}), 404
        except rs.InvalidRoomError as err:
            return jsonify({"error": str(err)}), 400

    @app.route("/api/rooms/<room_id>", methods=["DELETE"])
    @require_auth
    @require_role(auth.ROLE_STAFF)
    def api_delete_room(
        user: auth.User, room_id: str
    ) -> Tuple[Response, int]:
        """Delete an existing room (Staff only)."""
        try:
            rs.delete_room(app_rooms, room_id)
            if conn is not None:
                db.delete_room(conn, room_id)
            return jsonify({"message": f"Room {room_id} deleted."}), 200
        except rs.RoomNotFoundError as err:
            return jsonify({"error": str(err)}), 404

    @app.route("/api/rooms/<room_id>/unavailable", methods=["POST"])
    @require_auth
    @require_role(auth.ROLE_STAFF)
    def api_mark_unavailable(
        user: auth.User, room_id: str
    ) -> Tuple[Response, int]:
        """Mark a room closed for a date range (Staff only)."""
        data = request.get_json(silent=True) or {}
        raw_start = data.get("start_date")
        raw_end = data.get("end_date")
        reason = data.get("reason", "")
        if not raw_start or not raw_end:
            return jsonify({"error": "start_date and end_date required."}), 400
        try:
            start_d = parse_date(raw_start)
            end_d = parse_date(raw_end)
            period = rs.mark_room_unavailable(
                app_rooms, room_id, start_d, end_d, reason
            )
            if conn is not None:
                db.save_unavailable_period(conn, room_id, period)

            return jsonify({
                "message": "Room marked unavailable.",
                "unavailable_period": {
                    "start_date": period.start_date.isoformat(),
                    "end_date": period.end_date.isoformat(),
                    "reason": period.reason,
                },
            }), 201
        except ValueError:
            msg = "Invalid date format. Use YYYY-MM-DD."
            return jsonify({"error": msg}), 400
        except rs.RoomNotFoundError as err:
            return jsonify({"error": str(err)}), 404
        except rs.InvalidRoomError as err:
            return jsonify({"error": str(err)}), 400

    # ---------------------------------------------------------
    # Search & Recommendation Routes
    # ---------------------------------------------------------

    @app.route("/api/rooms/available", methods=["GET"])
    @require_auth
    def api_find_available(user: auth.User) -> Tuple[Response, int]:
        """Filter available rooms by capacity, equipment, and dates."""
        try:
            raw_group = request.args.get("group_size", "1")
            group_size = int(raw_group)
            start_d = parse_date(request.args.get("start_date", ""))
            end_d = parse_date(request.args.get("end_date", ""))
        except (ValueError, TypeError):
            return jsonify({
                "error": "Valid group_size and YYYY-MM-DD dates required."
            }), 400

        req_equipment: Dict[str, int] = {}
        for key in ("projector", "mic", "whiteboard", "tv_screen"):
            val = request.args.get(key)
            if val is not None and val.isdigit():
                req_equipment[key] = int(val)

        try:
            matched = rs.find_available_rooms(
                app_rooms, group_size, start_d, end_d, req_equipment
            )
            return jsonify({
                "rooms": [room_to_dict(r) for r in matched],
                "total": len(matched),
            }), 200
        except rs.InvalidRoomError as err:
            return jsonify({"error": str(err)}), 400

    @app.route("/api/rooms/recommend", methods=["GET"])
    @require_auth
    def api_recommend(user: auth.User) -> Tuple[Response, int]:
        """Recommend the optimal tightest-fitting room in O(n) time."""
        try:
            raw_group = request.args.get("group_size", "1")
            group_size = int(raw_group)
            start_d = parse_date(request.args.get("start_date", ""))
            end_d = parse_date(request.args.get("end_date", ""))
        except (ValueError, TypeError):
            return jsonify({
                "error": "Valid group_size and YYYY-MM-DD dates required."
            }), 400

        req_equipment: Dict[str, int] = {}
        for key in ("projector", "mic", "whiteboard", "tv_screen"):
            val = request.args.get(key)
            if val is not None and val.isdigit():
                req_equipment[key] = int(val)

        try:
            best = rs.recommend_room(
                app_rooms, group_size, start_d, end_d, req_equipment
            )
            res = room_to_dict(best) if best else None
            return jsonify({"recommended_room": res}), 200
        except rs.InvalidRoomError as err:
            return jsonify({"error": str(err)}), 400

    @app.route("/api/rooms/seed", methods=["POST"])
    @require_auth
    @require_role(auth.ROLE_STAFF)
    def api_seed_rooms(user: auth.User) -> Tuple[Response, int]:
        """Seed official CMKL campus classrooms (Staff only)."""
        load_cmkl_rooms(app_rooms)
        if conn is not None:
            for r in app_rooms.values():
                db.save_room(conn, r)

        return jsonify({
            "message": "Seeded official CMKL rooms.",
            "total_rooms": len(app_rooms),
        }), 200

    # ---------------------------------------------------------
    # Reservation Routes (OBJ-05, OBJ-06, OBJ-07, OBJ-08)
    # ---------------------------------------------------------

    @app.route("/api/reservations", methods=["GET"])
    @require_auth
    def list_reservations(user: auth.User) -> Tuple[Response, int]:
        """List all reservations, optionally filtered by room."""
        room_id = request.args.get("room_id")
        if room_id:
            res_list = app_res_repo.get_by_room(room_id)
        else:
            res_list = res_service.get_all_reservations()

        serialized = [reservation_to_dict(r) for r in res_list]
        return jsonify({
            "reservations": serialized,
            "total": len(serialized),
        }), 200

    @app.route("/api/reservations", methods=["POST"])
    @require_auth
    def api_create_reservation(user: auth.User) -> Tuple[Response, int]:
        """Create a reservation with conflict & capacity checks."""
        data = request.get_json(silent=True) or {}
        competency = data.get("competency", "")
        room_id = data.get("room_id", "")
        group_size = data.get("group_size", 0)
        raw_start_date = data.get("start_date", "")
        raw_end_date = data.get("end_date")
        raw_start_time = data.get("start_time", "")
        raw_end_time = data.get("end_time", "")
        repetition_str = data.get("repetition", "Weekly")

        try:
            group_size = int(group_size)
            start_d = parse_date(raw_start_date)
            end_d = parse_date(raw_end_date) if raw_end_date else None
            start_t = parse_time(raw_start_time)
            end_t = parse_time(raw_end_time)
            rep = rdata.Repetition(repetition_str)
        except (ValueError, TypeError) as err:
            return jsonify({"error": f"Invalid format: {str(err)}"}), 400

        candidate = rdata.Reservation(
            competency=competency,
            room_id=room_id,
            group_size=group_size,
            start_date=start_d,
            end_date=end_d,
            start_time=start_t,
            end_time=end_t,
            repetition=rep,
        )

        try:
            created = res_service.create_reservation(candidate)
            if conn is not None:
                db.save_reservation(conn, created)
            return jsonify({
                "message": "Reservation created successfully.",
                "reservation": reservation_to_dict(created),
            }), 201
        except (
            rservice.InvalidReservationError,
            rservice.CapacityExceededError,
        ) as err:
            return jsonify({"error": str(err)}), 400
        except rservice.RoomNotFoundError as err:
            return jsonify({"error": str(err)}), 404
        except rservice.ReservationConflictError as err:
            return jsonify({
                "error": str(err),
                "conflicting_reservation": reservation_to_dict(
                    err.conflicting_reservation
                ),
            }), 409

    @app.route("/api/reservations/search", methods=["GET"])
    @require_auth
    def api_search_reservations(user: auth.User) -> Tuple[Response, int]:
        """Search reservations by competency name."""
        query = request.args.get("competency", "")
        matched = res_service.search_by_competency(query)
        serialized = [reservation_to_dict(r) for r in matched]
        return jsonify({
            "reservations": serialized,
            "total": len(serialized),
        }), 200

    @app.route("/api/reservations/schedule", methods=["GET"])
    @require_auth
    def api_get_schedule(user: auth.User) -> Tuple[Response, int]:
        """View schedule for a specific week and optional room."""
        raw_week = request.args.get("week_start")
        if not raw_week:
            msg = "week_start (YYYY-MM-DD) query parameter required."
            return jsonify({"error": msg}), 400
        try:
            week_start = parse_date(raw_week)
        except ValueError:
            msg = "Invalid week_start format. Use YYYY-MM-DD."
            return jsonify({"error": msg}), 400

        room_id = request.args.get("room_id")
        schedule = res_service.get_schedule(week_start, room_id)
        serialized = [reservation_to_dict(r) for r in schedule]
        return jsonify({
            "week_start": week_start.isoformat(),
            "room_id": room_id,
            "schedule": serialized,
            "total": len(serialized),
        }), 200

    @app.route("/api/reservations/export", methods=["GET"])
    @require_auth
    def api_export_schedule(user: auth.User) -> Response:
        """Export schedule as a plain text timetable file."""
        raw_week = request.args.get("week_start")
        if not raw_week:
            return jsonify({"error": "week_start query required."}), 400
        try:
            week_start = parse_date(raw_week)
        except ValueError:
            msg = "Invalid week_start format. Use YYYY-MM-DD."
            return jsonify({"error": msg}), 400

        room_id = request.args.get("room_id")
        text_report = res_service.export_schedule_text(week_start, room_id)
        filename = f"schedule_{week_start.isoformat()}.txt"
        resp = Response(text_report, mimetype="text/plain; charset=utf-8")
        resp.headers["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )
        return resp

    @app.route("/api/reservations/<reservation_id>", methods=["GET"])
    @require_auth
    def api_get_reservation(
        user: auth.User, reservation_id: str
    ) -> Tuple[Response, int]:
        """Get details of a single reservation by ID."""
        try:
            res = res_service.get_reservation(reservation_id)
            return jsonify({"reservation": reservation_to_dict(res)}), 200
        except rservice.ReservationNotFoundError as err:
            return jsonify({"error": str(err)}), 404

    @app.route("/api/reservations/<reservation_id>", methods=["PUT"])
    @require_auth
    def api_edit_reservation(
        user: auth.User, reservation_id: str
    ) -> Tuple[Response, int]:
        """Update an existing reservation with conflict check."""
        existing = app_res_repo.get_by_id(reservation_id)
        if existing is None:
            msg = f"Reservation with ID '{reservation_id}' not found."
            return jsonify({"error": msg}), 404

        data = request.get_json(silent=True) or {}
        competency = data.get("competency", existing.competency)
        room_id = data.get("room_id", existing.room_id)
        group_size = data.get("group_size", existing.group_size)
        raw_start_date = data.get("start_date")
        raw_end_date = data.get("end_date")
        raw_start_time = data.get("start_time")
        raw_end_time = data.get("end_time")
        repetition_str = data.get("repetition")

        try:
            group_size = int(group_size)
            start_d = (
                parse_date(raw_start_date)
                if raw_start_date
                else existing.start_date
            )
            end_d = (
                parse_date(raw_end_date)
                if raw_end_date is not None
                else existing.end_date
            )
            start_t = (
                parse_time(raw_start_time)
                if raw_start_time
                else existing.start_time
            )
            end_t = (
                parse_time(raw_end_time)
                if raw_end_time
                else existing.end_time
            )
            rep = (
                rdata.Repetition(repetition_str)
                if repetition_str
                else existing.repetition
            )
        except (ValueError, TypeError) as err:
            return jsonify({"error": f"Invalid format: {str(err)}"}), 400

        updated = rdata.Reservation(
            reservation_id=reservation_id,
            competency=competency,
            room_id=room_id,
            group_size=group_size,
            start_date=start_d,
            end_date=end_d,
            start_time=start_t,
            end_time=end_t,
            repetition=rep,
        )

        try:
            saved = res_service.edit_reservation(updated)
            if conn is not None:
                db.save_reservation(conn, saved)
            return jsonify({
                "message": "Reservation updated successfully.",
                "reservation": reservation_to_dict(saved),
            }), 200
        except (
            rservice.InvalidReservationError,
            rservice.CapacityExceededError,
        ) as err:
            return jsonify({"error": str(err)}), 400
        except rservice.RoomNotFoundError as err:
            return jsonify({"error": str(err)}), 404
        except rservice.ReservationConflictError as err:
            return jsonify({
                "error": str(err),
                "conflicting_reservation": reservation_to_dict(
                    err.conflicting_reservation
                ),
            }), 409

    @app.route("/api/reservations/<reservation_id>", methods=["DELETE"])
    @require_auth
    def api_delete_reservation(
        user: auth.User, reservation_id: str
    ) -> Tuple[Response, int]:
        """Delete an existing reservation."""
        try:
            res_service.delete_reservation(reservation_id)
            if conn is not None:
                db.delete_reservation(conn, reservation_id)
            return jsonify({
                "message": f"Reservation {reservation_id} deleted."
            }), 200
        except rservice.ReservationNotFoundError as err:
            return jsonify({"error": str(err)}), 404

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
