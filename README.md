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

The **Classroom Reservation Application** streamlines semester classroom planning at CMKL University. It manages room capacities, specialized equipment attributes, closures/renovations, and conflict-free reservations for up to 50 competencies per semester.

### Key Capabilities
- **Authentication & RBAC**: Secure credential verification with role segregation (Staff vs Professor).
- **Room Management**: Add, edit, and delete bookable rooms with capacity and equipment attributes.
- **Availability & Closures**: Mark rooms unavailable during specific date ranges (e.g. renovations).
- **Search & Filtering**: Filter rooms by group size, required equipment, and date ranges in optimal $O(n)$ time.
- **Smart Recommendation**: Auto-recommend the smallest suitable room to optimize campus resource utilization.
- **Reservation Engine**: Create, edit, and delete semester reservations with automatic conflict checks for overlapping times and room capacities.
- **Schedule Views & Timetable Export**: View weekly schedules (handling parallel classes in different rooms) and export formatted schedule reports to text files.
- **Permanent Persistence**: SQLite database (`app.db`) for retaining campus records across semesters / 4-year cycle.

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

## Quick Start & Installation (< 3 Minutes)

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

### 3. Start the API Gateway (Backend Server)
```bash
python ApiGateway/api_gateway.py
```
Server runs at `http://127.0.0.1:5000` with CORS enabled for the React frontend.

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
- `POST   /api/rooms/seed` — Seed official CMKL classrooms (Staff only)

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

### Run All 129 Unit Tests
```bash
python -m unittest discover -s RoomService -p "test_*.py"
python -m unittest discover -s AuthService -p "test_*.py"
python -m unittest discover -s ApiGateway -p "test_*.py"
python -m unittest discover -s Database -p "test_*.py"
python -m unittest discover -s Reservation -p "test_*.py"
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

