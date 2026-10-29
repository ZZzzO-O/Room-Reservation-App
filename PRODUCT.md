# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary**: Professors and instructors at CMKL University reserving classrooms and labs for up to 50 course competencies per semester.
- **Secondary**: Academic staff and administrators managing room inventories, capacities, equipment records, and closure periods (maintenance/renovations).

## Product Purpose

Streamlines semester classroom allocation and timetable scheduling at CMKL University. It ensures conflict-free room reservations, enforces room capacity and equipment constraints, and optimizes physical campus resource utilization.

## Positioning

An academic operations management system designed for institutional scheduling precision and constraint verification, prioritizing schedule density, conflict prevention, and equipment readiness over consumer marketing or generic SaaS tropes.

## Operating Context

- Used in faculty offices, academic administration desks, and classroom podiums.
- Environment: Academic desktop/laptop browsers under indoor office lighting, requiring rapid scanning of timetables, room availability lists, and equipment manifests.
- Mode: **Operate** (task-driven utility, scanability, consistency, and restrained institutional authority).

## Capabilities and Constraints

- **Role-Based Access Control**: Staff (full catalog and closure management) vs. Professor (booking, search, timetable viewing).
- **Conflict Prevention Engine**: Instant verification against overlapping bookings, time boundaries, and capacity limits.
- **Equipment Matching**: Exact inventory tracking (projectors, whiteboards, computer counts, audio gear).
- **Room Closures**: Explicit date-range closures with recorded reasons (maintenance/renovation).
- **Recommendation Engine**: Automatically selects the smallest suitable room meeting class size to prevent campus resource waste.
- **Timetable Views & Export**: Weekly schedule view with parallel booking handling and plain-text report export.
- **Persistence**: SQLite database (`app.db`) via Python microservices backend (FastAPI/Flask API Gateway).

## Brand Commitments

- **Institution**: CMKL University (Course: SEN-201 Software Engineering Processes, Team Vibranium).
- **Tone**: Clean, academic, precise, trustworthy, and utilitarian. Free of generic AI aesthetics (no gratuitous blue/indigo gradients, bouncy animations, or nested card padding).

## Evidence on Hand

- Verified API Gateway, AuthService, RoomService, ReservationService, and SQLite database in repository.
- React frontend in [reservation-app/src](file:///e:/University%20Projects/Room_Reservation/reservation-app/src).
- Seed data with real classroom numbering, capacities, and course competencies.

## Product Principles

1. **Information Density Over Decoration**: Academic users need to see room capacity, equipment status, and schedule slots at a glance without pagination or excessive card padding.
2. **Deterministic Conflict Clarity**: Errors and availability states must be explicit, precise, and immediate—never hidden behind decorative badges or vague toasts.
3. **Restrained Institutional Craft**: Treat the application as serious university infrastructure with purpose-built data tables, clean typography, and purposeful contrast.
