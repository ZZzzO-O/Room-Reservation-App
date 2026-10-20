# file: api_gateway.py
# purpose: REST API Gateway and Network Service routing for the web app
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

from datetime import date
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
sys.path.insert(0, str(BASE_DIR / "Database"))

import auth_service as auth  # noqa: E402
import database as db  # noqa: E402
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


def create_app(
    users: Optional[Dict[str, auth.User]] = None,
    sessions: Optional[Dict[str, auth.Session]] = None,
    rooms: Optional[Dict[str, rs.Room]] = None,
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

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
