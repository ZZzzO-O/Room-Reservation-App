# Classroom Reservation Application

**Course**: SEN-201 Software Engineering Processes (Fall 2026)  
**Team**: Vibranium  
**Members**:
- Sittipruk Puttisarn (Jan) — Reservation Service & Reservation Data
- Su Pyae Pyae Aung (Micky) — Room Service & Room Data
- Zin Zin Zaw Win (Zin Zin) — Client UI & App Executive
- Thiri Htet Thwe (Thiri) — API Gateway, Network Service, Auth Service & User Data

---

## Overview

A room booking system for CMKL University. Staff maintain the list of rooms (capacity,
equipment, closures for renovation); professors book rooms for their courses, up to 50
course competencies per semester, and the system rejects double bookings and groups that
don't fit.

### What it does
- **Sign-in with roles**: Staff and Professor accounts; only Staff can change rooms.
- **Rooms**: add, edit and delete rooms with capacity and equipment counts; rooms with reservations cannot be deleted, and capacity cannot be reduced below an existing reservation's group size.
- **Closures**: close a room for a date range with a reason (e.g. renovation).
- **Search**: filter rooms by group size, required equipment and dates.
- **Recommendation**: suggests the smallest room that fits the group.
- **Reservations**: create, edit and delete bookings; overlapping times and over-capacity groups are rejected.
- **Weekly schedule**: timetable view (parallel classes in different rooms are fine) with a plain-text export.
- **Storage**: SQLite (`app.db`), so data survives restarts.

---

## System Architecture

```text
 [ Client UI (React) ]
         │
         ▼
 [ Network Service & API Gateway ] ◄──► [ Auth Service & User Data ]
         │
    ┌────┴─────────────────────────────┐
    ▼                                  ▼
 [ Room Service ]             [ Reservation Service ]
    │                                  │
    ▼                                  ▼
 [ Room Data & Closures ]     [ Reservation Data ]
    │                                  │
    └─────────────────┬────────────────┘
                      ▼
            [ SQLite DB (app.db) ]
```

---

## Getting started

### Prerequisites
- Python 3.10+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/ZZzzO-O/Room-Reservation-App.git
cd Room-Reservation-App
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the API gateway
```bash
python ApiGateway/api_gateway.py
```
Server runs at `http://127.0.0.1:5000` with CORS enabled for the React frontend.

### 4. Start the web app
See [reservation-app/README.md](reservation-app/README.md) (needs Node.js 20.19+ or 22.12+).

---

## REST API Endpoints

### Authentication
- `POST /api/auth/login` — Log in and obtain session token
- `POST /api/auth/logout` — Revoke session token
- `GET  /api/auth/me` — Current user profile

### Rooms
- `GET    /api/rooms` — List all registered rooms
- `POST   /api/rooms` — Create room (Staff only)
- `GET    /api/rooms/<id>` — View single room details
- `PUT    /api/rooms/<id>` — Update room details (Staff only)
- `DELETE /api/rooms/<id>` — Delete room (Staff only)
- `POST   /api/rooms/<id>/unavailable` — Mark room closed with date range & reason (Staff only)
- `GET    /api/rooms/available` — Filter available rooms by group size, equipment & dates
- `GET    /api/rooms/recommend` — Recommend tightest-fit room
- `POST   /api/rooms/seed` — Load the CMKL seed rooms (Staff only)

### Reservations & Schedule
- `GET    /api/reservations` — List reservations (optional `?room_id=...`)
- `POST   /api/reservations` — Create reservation (conflict & capacity checked)
- `GET    /api/reservations/<id>` — View single reservation
- `PUT    /api/reservations/<id>` — Update reservation (conflict checked)
- `DELETE /api/reservations/<id>` — Cancel/delete reservation
- `GET    /api/reservations/search` — Search reservations by competency (`?competency=...`)
- `GET    /api/reservations/schedule` — View weekly timetable (`?week_start=YYYY-MM-DD[&room_id=...]`)
- `GET    /api/reservations/export` — Download weekly schedule as text file

---

## Testing & Quality Assurance

### Run all 129 unit tests
```bash
python -m unittest discover -s RoomService -p "test_*.py"
python -m unittest discover -s AuthService -p "test_*.py"
python -m unittest discover -s ApiGateway -p "test_*.py"
python -m unittest discover -s Database -p "test_*.py"
python -m unittest discover -s Reservation -p "test_*.py"
python -m unittest test_desktop_app
```

### Run Coding Standard Lint Checks (PEP 8, 79-character limit)
```bash
flake8 --max-line-length=79 RoomService AuthService ApiGateway Database Reservation
```

### Run Test Coverage
```bash
coverage erase
coverage run -a --source=RoomService -m unittest discover -s RoomService -p "test_*.py"
coverage run -a --source=AuthService -m unittest discover -s AuthService -p "test_*.py"
coverage run -a --source=ApiGateway -m unittest discover -s ApiGateway -p "test_*.py"
coverage run -a --source=Database -m unittest discover -s Database -p "test_*.py"
coverage run -a --source=Reservation -m unittest discover -s Reservation -p "test_*.py"
coverage report -m
```
