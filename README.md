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
- **Conflict Detection**: Prevent overlapping bookings and validate room capacities against student group sizes.

---

## System Architecture

```text
 [ Client UI (React) ]
         │
         ▼
 [ Network Service & API Gateway ] ◄──► [ Auth Service & User Data ]
         │
    ┌────┴─────────────────┐
    ▼                      ▼
 [ Room Service ]   [ Reservation Service ]
    │                      │
    ▼                      ▼
 [ Room Data ]      [ Reservation Data ]
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

## Testing & Quality Assurance

### Run All Unit Tests (86 tests across all services)
```bash
python -m unittest discover -s RoomService
python -m unittest discover -s AuthService
python -m unittest discover -s ApiGateway
```

### Run Coding Standard Lint Checks (PEP 8, 79-character limit)
```bash
flake8 --max-line-length=79 RoomService AuthService ApiGateway
```

### Run Test Coverage
```bash
coverage run -m unittest discover -s RoomService
coverage run -a -m unittest discover -s AuthService
coverage run -a -m unittest discover -s ApiGateway
coverage report -m
```
