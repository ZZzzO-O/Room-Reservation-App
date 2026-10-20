# file: demo.py
# purpose: Quick demonstration of RoomService features and CMKL seed data
# author: Su Pyae Pyae Aung (Micky)
# date: 2026-10-20

from datetime import date
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import room_service as rs  # noqa: E402
from seed_rooms import load_cmkl_rooms  # noqa: E402


def main() -> None:
    """Run an interactive demonstration of Room Service."""
    print("=" * 65)
    print("  CMKL CLASSROOM RESERVATION SYSTEM - ROOM SERVICE DEMO")
    print("=" * 65)

    # 1. Initialize and seed rooms
    rooms = {}
    load_cmkl_rooms(rooms)
    print(f"\n[1] Seeded {len(rooms)} official CMKL classrooms into database:")
    for r in rooms.values():
        eq_str = ", ".join(f"{k} x{v}" for k, v in r.equipment.items())
        print(f"    - Room {r.room_id:<4} {r.name:<9} | "
              f"Cap: {r.capacity:<2} | {eq_str}")

    # 2. Mark Room 608 (Bridge) unavailable for renovation
    closure_start = date(2026, 11, 2)
    closure_end = date(2026, 11, 6)
    rs.mark_room_unavailable(
        rooms,
        room_id="608",
        start_date=closure_start,
        end_date=closure_end,
        reason="Acoustic panel maintenance",
    )
    print(f"\n[2] Marked Room 608 (Bridge) UNAVAILABLE from {closure_start} "
          f"to {closure_end}:")
    print(f"    Reason: '{rooms['608'].unavailable_periods[0].reason}'")

    # 3. Filter available rooms for 35 students needing a projector
    print(f"\n[3] Searching available rooms for 35 students needing >= 1 "
          f"projector ({closure_start} to {closure_end}):")
    matching = rs.find_available_rooms(
        rooms=rooms,
        group_size=35,
        start_date=closure_start,
        end_date=closure_end,
        required_equipment={"projector": 1},
    )
    for r in matching:
        print(f"    [OK] Room {r.room_id:<4} {r.name:<9} "
              f"(Cap: {r.capacity}) fits criteria")
    print("    (Notice: Room 608 Bridge is omitted because it is closed)")

    # 4. Recommend the best room
    best = rs.recommend_room(
        rooms=rooms,
        group_size=35,
        start_date=closure_start,
        end_date=closure_end,
        required_equipment={"projector": 1},
    )
    if best:
        print("\n[4] SMART RECOMMENDATION (Tightest fit in O(n) time):")
        print(f"    [*] Room {best.room_id} ({best.name})")
        print(f"        Capacity: {best.capacity} (Closest to required 35)")
        print(f"        Equipment: {best.equipment}")

    print("\n" + "=" * 65)
    print("  All operations completed successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
