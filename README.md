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

## Public demo deployment (Render)

The repository includes a Docker-based Render Blueprint (`render.yaml`) configured
for Render's free web-service plan. To deploy:

1. Push the project to GitHub, including `Dockerfile`, `.dockerignore`,
   `requirements-render.txt`, `wsgi.py`, and `render.yaml`. Do not add `app.db`.
2. In Render, choose **New → Blueprint**, connect the repository and branch,
   and confirm the service is on the **Free** plan.
3. Wait for the Docker build and health check to succeed, then open the
   `onrender.com` URL shown in the Render dashboard.
4. Test login, booking, and page refresh using fictional demo data only.

The current application seeds documented test accounts and is intended for
class demonstrations, not real public reservations. Anyone with the URL can
reach the login page, and the published demo credentials must not be used for
private data. The free service uses an ephemeral SQLite path: reservations
may be lost when Render spins the service down, restarts it, or deploys a new
version. The service may also take about a minute to wake after inactivity.
Do not use this deployment for important or real reservations. Persistent
storage requires a paid service. Remove or secure demo account seeding and
offline frontend fallbacks before using this deployment for real users.

### Open or install the web app

Open the Render HTTPS URL in a supported browser; installing is optional.
Desktop Chrome/Edge users can choose **Install app** or **Create shortcut** in
the browser menu. Android Chrome offers **Install app** or **Add to Home
screen**; on iPhone/iPad, open the URL in Safari and select **Share → Add to
Home Screen**. The PWA caches the application shell and static assets, but
reservations and other API operations require a network connection.

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
