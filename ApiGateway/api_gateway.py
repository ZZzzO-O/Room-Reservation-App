# file: api_gateway.py
# purpose: API Gateway + Network Service: receive HTTP requests, check the
#          login token with the Auth Service, and route to the right service
# author: Thiri Htet Thwe (Thiri)
# date: 2026-10-20

from dataclasses import dataclass
from datetime import date, time
from functools import wraps
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any, Callable, Dict, Optional, Tuple

from flask import Blueprint, Flask, Response, current_app, g, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent.parent
for folder in ("RoomService", "AuthService", "Reservation", "Database"):
    sys.path.insert(0, str(BASE_DIR / folder))

import auth_service as auth  # noqa: E402
import database as db  # noqa: E402
import reservation_data as rdata  # noqa: E402
import reservation_service as rservice  # noqa: E402
import room_service as rs  # noqa: E402
from seed_rooms import load_cmkl_rooms  # noqa: E402
from seed_users import load_test_users  # noqa: E402

EQUIPMENT_KEYS = ("projector", "mic", "whiteboard", "tv_screen")

# Which HTTP status each service error becomes. Flask picks the most
# specific match, so subclasses are handled correctly.
ERROR_STATUS = {
    ValueError: 400,
    TypeError: 400,
    auth.InvalidCredentialsError: 401,
    auth.InvalidSessionError: 401,
    rs.InvalidRoomError: 400,
    rs.RoomNotFoundError: 404,
    rs.DuplicateRoomError: 409,
    rservice.InvalidReservationError: 400,
    rservice.CapacityExceededError: 400,
    rservice.RoomNotFoundError: 404,
    rdata.ReservationNotFoundError: 404,
}

api = Blueprint("api", __name__, url_prefix="/api")


@dataclass
class AppState:
    """Everything the routes need, created once by create_app()."""

    auth: auth.AuthService
    rooms: Dict[str, rs.Room]
    reservations: rdata.ReservationRepository
    booking: rservice.ReservationService
    conn: sqlite3.Connection


class RoomCapacityLookup:
    """Lets the Reservation Service ask for a room's capacity."""

    def __init__(self, rooms: Dict[str, rs.Room]) -> None:
        """
        Keep a reference to the shared room dictionary.

        Args:
            rooms (Dict[str, rs.Room]): Rooms keyed by room id.
        """
        self.rooms = rooms

    def get_room_capacity(self, room_id: str) -> Optional[int]:
        """
        Return the room's capacity, or None if the room does not exist.

        Args:
            room_id (str): Room id.

        Returns:
            Optional[int]: Capacity, or None.
        """
        room = self.rooms.get(room_id)
        return room.capacity if room else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def state() -> AppState:
    """
    Return the shared state of the running app.

    Returns:
        AppState: Shared services and data.
    """
    return current_app.config["STATE"]


def error(message: str, status: int) -> Tuple[Response, int]:
    """
    Build the standard JSON error response.

    Args:
        message (str): Message shown to the user.
        status (int): HTTP status code.

    Returns:
        Tuple[Response, int]: {"error": message} and the status.
    """
    return jsonify({"error": message}), status


def body() -> Dict[str, Any]:
    """
    Return the request's JSON body, or {} if there is none.

    Returns:
        Dict[str, Any]: Parsed JSON body.
    """
    return request.get_json(silent=True) or {}


def save(save_function: Callable, *args: Any) -> None:
    """
    Write a change to SQLite.

    TODO(team): move these writes into the Room and Reservation services so
    the gateway never touches the database (reviewer feedback, Lab 5).

    Args:
        save_function (Callable): A database.py function taking conn first.
        *args (Any): The other arguments for that function.
    """
    save_function(state().conn, *args)


def user_to_dict(user: auth.User) -> Dict[str, str]:
    """
    Convert a User to JSON, leaving out the password hash and salt.

    Args:
        user (auth.User): User to convert.

    Returns:
        Dict[str, str]: Public user fields.
    """
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
    }


def room_to_dict(room: rs.Room) -> Dict[str, Any]:
    """
    Convert a Room to JSON.

    Args:
        room (rs.Room): Room to convert.

    Returns:
        Dict[str, Any]: Room fields, with dates as YYYY-MM-DD strings.
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


def reservation_to_dict(res: rdata.Reservation) -> Dict[str, Any]:
    """
    Convert a Reservation to JSON.

    Args:
        res (rdata.Reservation): Reservation to convert.

    Returns:
        Dict[str, Any]: Reservation fields as JSON-friendly values.
    """
    return {
        "reservation_id": res.reservation_id,
        "competency": res.competency,
        "room_id": res.room_id,
        "group_size": res.group_size,
        "start_date": res.start_date.isoformat(),
        "end_date": res.end_date.isoformat() if res.end_date else None,
        "start_time": res.start_time.strftime("%H:%M"),
        "end_time": res.end_time.strftime("%H:%M"),
        "day_of_week": res.day_of_week.value,
        "repetition": res.repetition.value,
    }


def to_date(text: Any) -> date:
    """
    Convert "YYYY-MM-DD" text to a date.

    Args:
        text (Any): Text from the request.

    Returns:
        date: Parsed date.

    Raises:
        ValueError: If the text is not a valid date.
    """
    try:
        return date.fromisoformat(str(text).strip())
    except ValueError:
        raise ValueError(f"Invalid date '{text}'. Use YYYY-MM-DD.") from None


def to_time(text: Any) -> time:
    """
    Convert "HH:MM" text to a time.

    Args:
        text (Any): Text from the request.

    Returns:
        time: Parsed time.

    Raises:
        ValueError: If the text is not a valid time.
    """
    try:
        return time.fromisoformat(str(text).strip())
    except ValueError:
        raise ValueError(f"Invalid time '{text}'. Use HH:MM.") from None


def to_int(text: Any) -> int:
    """
    Convert text such as "30" to a whole number.

    Args:
        text (Any): Text or number from the request.

    Returns:
        int: Parsed number.

    Raises:
        ValueError: If the text is not a whole number.
    """
    try:
        return int(text)
    except (TypeError, ValueError):
        raise ValueError(f"'{text}' is not a whole number.") from None


def search_args() -> Tuple[int, date, date, Dict[str, int]]:
    """
    Read room-search options from the URL query string.

    Returns:
        Tuple[int, date, date, Dict[str, int]]:
            group size, start date, end date, required equipment.

    Raises:
        ValueError: If group_size or a date is missing or badly formed.
    """
    args = request.args
    equipment = {
        key: int(args[key])
        for key in EQUIPMENT_KEYS
        if args.get(key, "").isdigit()
    }
    return (
        to_int(args.get("group_size", "1")),
        to_date(args.get("start_date", "")),
        to_date(args.get("end_date", "")),
        equipment,
    )


def reservation_from_json(
    data: Dict[str, Any], old: Optional[rdata.Reservation] = None
) -> rdata.Reservation:
    """
    Build a Reservation from a request body.

    When creating (old is None), missing dates/times are an error.
    When editing, any field left out keeps its old value.

    Args:
        data (Dict[str, Any]): Request body.
        old (Optional[rdata.Reservation]): Reservation being edited.

    Returns:
        rdata.Reservation: The new or updated reservation (not saved yet).

    Raises:
        ValueError: If a required field is missing or badly formed.
    """
    def read(
        key: str, parse: Callable, default: Any = None, required: bool = False
    ) -> Any:
        """Read one field: parse it, or fall back to old/default value."""
        raw = data.get(key)
        if raw not in (None, ""):
            return parse(raw)
        if old is not None:
            return getattr(old, key)
        if required:
            raise ValueError(f"{key} is required.")
        return default

    return rdata.Reservation(
        competency=read("competency", str, ""),
        room_id=read("room_id", str, ""),
        group_size=read("group_size", to_int, 0),
        start_date=read("start_date", to_date, required=True),
        end_date=read("end_date", to_date),
        start_time=read("start_time", to_time, required=True),
        end_time=read("end_time", to_time, required=True),
        repetition=read("repetition", rdata.Repetition,
                        rdata.Repetition.WEEKLY),
        reservation_id=old.reservation_id if old else None,
    )


# ---------------------------------------------------------------------------
# Access checks (decorators)
# ---------------------------------------------------------------------------

def login_required(view: Callable) -> Callable:
    """
    Reject the request with 401 unless it carries a valid token.

    The logged-in user is stored in g.user for the route to use.

    Args:
        view (Callable): Route function to protect.

    Returns:
        Callable: Wrapped route function.
    """
    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        header = request.headers.get("Authorization", "")
        g.token = header.removeprefix("Bearer ").strip()
        g.user = state().auth.check_token(g.token)
        return view(*args, **kwargs)
    return wrapper


def staff_only(view: Callable) -> Callable:
    """
    Reject the request with 403 unless the user is Staff.

    Must be listed below @login_required.

    Args:
        view (Callable): Route function to protect.

    Returns:
        Callable: Wrapped route function.
    """
    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if g.user.role != auth.ROLE_STAFF:
            return error("Forbidden: Staff privileges required.", 403)
        return view(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@api.post("/auth/login")
def login() -> Tuple[Response, int]:
    """Log in and return a session token."""
    data = body()
    user, session = state().auth.login(
        data.get("email", ""), data.get("password", "")
    )
    return jsonify({
        "token": session.token,
        "user": user_to_dict(user),
        "expires_at": session.expires_at.isoformat(),
    }), 200


@api.post("/auth/logout")
@login_required
def logout() -> Tuple[Response, int]:
    """End the current session."""
    state().auth.logout(g.token)
    return jsonify({"message": "Logged out successfully."}), 200


@api.get("/auth/me")
@login_required
def me() -> Tuple[Response, int]:
    """Return the logged-in user (same shape as the login response)."""
    return jsonify({"user": user_to_dict(g.user)}), 200


# ---------------------------------------------------------------------------
# Room routes
# ---------------------------------------------------------------------------

@api.get("/rooms")
@login_required
def list_rooms() -> Tuple[Response, int]:
    """List all rooms."""
    rooms = [room_to_dict(room) for room in state().rooms.values()]
    return jsonify({"rooms": rooms, "total": len(rooms)}), 200


@api.post("/rooms")
@login_required
@staff_only
def create_room() -> Tuple[Response, int]:
    """Add a room (Staff only)."""
    data = body()
    room = rs.create_room(
        state().rooms,
        room_id=data.get("room_id"),
        capacity=data.get("capacity"),
        equipment=data.get("equipment", {}),
        name=data.get("name", ""),
    )
    save(db.save_room, room)
    return jsonify({
        "message": "Room created successfully.",
        "room": room_to_dict(room),
    }), 201


@api.get("/rooms/<room_id>")
@login_required
def get_room(room_id: str) -> Tuple[Response, int]:
    """Show one room."""
    room = rs.get_room(state().rooms, room_id)
    return jsonify({"room": room_to_dict(room)}), 200


@api.put("/rooms/<room_id>")
@login_required
@staff_only
def edit_room(room_id: str) -> Tuple[Response, int]:
    """Change a room's capacity, equipment, or name (Staff only)."""
    data = body()
    room = rs.edit_room(
        state().rooms,
        room_id=room_id,
        capacity=data.get("capacity"),
        equipment=data.get("equipment"),
        name=data.get("name"),
    )
    save(db.save_room, room)
    return jsonify({
        "message": "Room updated successfully.",
        "room": room_to_dict(room),
    }), 200


@api.delete("/rooms/<room_id>")
@login_required
@staff_only
def delete_room(room_id: str) -> Tuple[Response, int]:
    """Delete a room (Staff only)."""
    rs.delete_room(state().rooms, room_id)
    save(db.delete_room, room_id)
    return jsonify({"message": f"Room {room_id} deleted."}), 200


@api.post("/rooms/<room_id>/unavailable")
@login_required
@staff_only
def mark_unavailable(room_id: str) -> Tuple[Response, int]:
    """Close a room for a date range (Staff only)."""
    data = body()
    period = rs.mark_room_unavailable(
        state().rooms,
        room_id,
        to_date(data.get("start_date", "")),
        to_date(data.get("end_date", "")),
        data.get("reason", ""),
    )
    save(db.save_unavailable_period, room_id, period)
    return jsonify({
        "message": "Room marked unavailable.",
        "unavailable_period": {
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "reason": period.reason,
        },
    }), 201


@api.get("/rooms/available")
@login_required
def available_rooms() -> Tuple[Response, int]:
    """List rooms that fit the group, have the equipment, and are open."""
    rooms = rs.find_available_rooms(state().rooms, *search_args())
    return jsonify({
        "rooms": [room_to_dict(room) for room in rooms],
        "total": len(rooms),
    }), 200


@api.get("/rooms/recommend")
@login_required
def recommend_room() -> Tuple[Response, int]:
    """Suggest the smallest room that fits."""
    best = rs.recommend_room(state().rooms, *search_args())
    return jsonify({
        "recommended_room": room_to_dict(best) if best else None
    }), 200


@api.post("/rooms/seed")
@login_required
@staff_only
def seed_rooms() -> Tuple[Response, int]:
    """Load the standard CMKL rooms (Staff only)."""
    load_cmkl_rooms(state().rooms)
    for room in state().rooms.values():
        save(db.save_room, room)
    return jsonify({
        "message": "Seeded official CMKL rooms.",
        "total_rooms": len(state().rooms),
    }), 200


# ---------------------------------------------------------------------------
# Reservation routes
# ---------------------------------------------------------------------------

@api.get("/reservations")
@login_required
def list_reservations() -> Tuple[Response, int]:
    """List reservations, optionally only for one room."""
    room_id = request.args.get("room_id")
    found = (
        state().reservations.get_by_room(room_id)
        if room_id
        else state().booking.get_all_reservations()
    )
    items = [reservation_to_dict(res) for res in found]
    return jsonify({"reservations": items, "total": len(items)}), 200


@api.post("/reservations")
@login_required
def create_reservation() -> Tuple[Response, int]:
    """Book a room; the Reservation Service checks conflicts and size."""
    created = state().booking.create_reservation(
        reservation_from_json(body())
    )
    save(db.save_reservation, created)
    return jsonify({
        "message": "Reservation created successfully.",
        "reservation": reservation_to_dict(created),
    }), 201


@api.get("/reservations/search")
@login_required
def search_reservations() -> Tuple[Response, int]:
    """Find reservations by competency name."""
    found = state().booking.search_by_competency(
        request.args.get("competency", "")
    )
    items = [reservation_to_dict(res) for res in found]
    return jsonify({"reservations": items, "total": len(items)}), 200


@api.get("/reservations/schedule")
@login_required
def schedule() -> Tuple[Response, int]:
    """Show one week's schedule, optionally for one room."""
    week_start = to_date(request.args.get("week_start", ""))
    room_id = request.args.get("room_id")
    items = [
        reservation_to_dict(res)
        for res in state().booking.get_schedule(week_start, room_id)
    ]
    return jsonify({
        "week_start": week_start.isoformat(),
        "room_id": room_id,
        "schedule": items,
        "total": len(items),
    }), 200


@api.get("/reservations/export")
@login_required
def export_schedule() -> Response:
    """Download one week's schedule as a text file."""
    week_start = to_date(request.args.get("week_start", ""))
    text = state().booking.export_schedule_text(
        week_start, request.args.get("room_id")
    )
    filename = f"schedule_{week_start.isoformat()}.txt"
    return Response(
        text,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api.get("/reservations/<reservation_id>")
@login_required
def get_reservation(reservation_id: str) -> Tuple[Response, int]:
    """Show one reservation."""
    res = state().booking.get_reservation(reservation_id)
    return jsonify({"reservation": reservation_to_dict(res)}), 200


@api.put("/reservations/<reservation_id>")
@login_required
def edit_reservation(reservation_id: str) -> Tuple[Response, int]:
    """Change a reservation; fields left out keep their old values."""
    old = state().booking.get_reservation(reservation_id)
    saved = state().booking.edit_reservation(
        reservation_from_json(body(), old)
    )
    save(db.save_reservation, saved)
    return jsonify({
        "message": "Reservation updated successfully.",
        "reservation": reservation_to_dict(saved),
    }), 200


@api.delete("/reservations/<reservation_id>")
@login_required
def delete_reservation(reservation_id: str) -> Tuple[Response, int]:
    """Delete a reservation."""
    state().booking.delete_reservation(reservation_id)
    save(db.delete_reservation, reservation_id)
    return jsonify({
        "message": f"Reservation {reservation_id} deleted."
    }), 200


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

def register_error_handlers(app: Flask) -> None:
    """
    Turn service errors into JSON error responses in one place.

    Args:
        app (Flask): The app to configure.
    """
    for error_type, status in ERROR_STATUS.items():
        app.register_error_handler(
            error_type,
            lambda err, status=status: error(str(err), status),
        )

    @app.errorhandler(rservice.ReservationConflictError)
    def conflict(err: rservice.ReservationConflictError) -> Any:
        """Return 409 plus the reservation that is in the way."""
        return jsonify({
            "error": str(err),
            "conflicting_reservation": reservation_to_dict(
                err.conflicting_reservation
            ),
        }), 409


def load_data(conn: sqlite3.Connection) -> AppState:
    """
    Load all data from SQLite, adding sample rooms and users if empty.

    Args:
        conn (sqlite3.Connection): Open database.

    Returns:
        AppState: All services, ready to use.
    """
    rooms = db.load_rooms(conn)
    if not rooms:
        load_cmkl_rooms(rooms)
        for room in rooms.values():
            db.save_room(conn, room)

    reservations = rdata.ReservationRepository()
    for res in db.load_reservations(conn).values():
        reservations.add_reservation(res)

    auth_service = auth.AuthService(conn)
    if not auth_service.users:
        load_test_users(auth_service)

    return AppState(
        auth=auth_service,
        rooms=rooms,
        reservations=reservations,
        booking=rservice.ReservationService(
            reservations, RoomCapacityLookup(rooms)
        ),
        conn=conn,
    )


def create_app(db_path: str = str(BASE_DIR / db.DEFAULT_DB_FILE)) -> Flask:
    """
    Build the Flask app.

    Args:
        db_path (str): SQLite file, or ":memory:" for a throwaway database
            (used by tests).

    Returns:
        Flask: The configured app.
    """
    conn = db.get_connection(db_path)
    db.init_db(conn)

    app = Flask(__name__)
    CORS(app)
    app.config["STATE"] = load_data(conn)
    app.register_blueprint(api)
    register_error_handlers(app)

    @app.get("/")
    def root() -> Tuple[Response, int]:
        """Health check: lists every endpoint."""
        endpoints = sorted(
            f"{method} {rule.rule}"
            for rule in app.url_map.iter_rules()
            if rule.rule.startswith("/api")
            for method in rule.methods - {"HEAD", "OPTIONS"}
        )
        return jsonify({
            "name": "CMKL Classroom Reservation API Gateway",
            "status": "online",
            "endpoints": endpoints,
        }), 200

    return app


if __name__ == "__main__":
    # Debug mode lets anyone who can reach the server run code, so it is off
    # unless FLASK_DEBUG=1, and the server only listens on this computer.
    create_app().run(
        host="127.0.0.1",
        port=5000,
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
