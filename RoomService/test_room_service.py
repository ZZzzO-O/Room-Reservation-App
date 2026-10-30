# file: test_room_service.py
# purpose: Unit tests for room_service.py
# author: Su Pyae Pyae Aung (Micky)
# date: 2026-10-06
"""Unit test suite for RoomService and seed rooms."""

from datetime import date
import unittest

import room_service as rs
from seed_rooms import load_cmkl_rooms


class RoomTestCase(unittest.TestCase):
    """Base class that gives each test a fresh room data store."""

    def setUp(self) -> None:
        """Create an empty room store before every test."""
        self.rooms = {}


class TestCreateRoom(RoomTestCase):
    """Tests for create_room."""

    def test_create_room_stores_room(self) -> None:
        """Check: create room stores room."""
        room = rs.create_room(self.rooms, "A101", 40, {"projector": 1})
        self.assertIs(self.rooms["A101"], room)
        self.assertEqual(room.capacity, 40)
        self.assertEqual(room.equipment, {"projector": 1})
        self.assertEqual(room.name, "")

    def test_create_room_with_name(self) -> None:
        """Check: create room with human-readable name."""
        room = rs.create_room(
            self.rooms, "601", 40, {"projector": 1}, name="Pioneer"
        )
        self.assertEqual(room.room_id, "601")
        self.assertEqual(room.name, "Pioneer")

    def test_create_room_without_equipment_defaults_to_empty(self) -> None:
        """Check: create room without equipment defaults to empty."""
        room = rs.create_room(self.rooms, "A101", 40)
        self.assertEqual(room.equipment, {})

    def test_create_room_copies_equipment_dict(self) -> None:
        """Check: create room copies equipment dict."""
        equipment = {"projector": 1}
        room = rs.create_room(self.rooms, "A101", 40, equipment)
        equipment["projector"] = 9
        self.assertEqual(room.equipment["projector"], 1)

    def test_duplicate_id_rejected(self) -> None:
        """Check: duplicate id rejected."""
        rs.create_room(self.rooms, "A101", 40)
        with self.assertRaises(rs.DuplicateRoomError):
            rs.create_room(self.rooms, "A101", 20)

    def test_empty_id_rejected(self) -> None:
        """Check: empty id rejected."""
        for bad_id in ("", "   "):
            with self.assertRaises(rs.InvalidRoomError):
                rs.create_room(self.rooms, bad_id, 40)

    def test_non_string_id_rejected(self) -> None:
        """Check: non-string id rejected."""
        for bad_id in (101, None, ["A101"]):
            with self.assertRaises(rs.InvalidRoomError):
                rs.create_room(self.rooms, bad_id, 40)

    def test_non_string_name_rejected(self) -> None:
        """Check: non-string room name rejected."""
        with self.assertRaises(rs.InvalidRoomError):
            rs.create_room(self.rooms, "A101", 40, name=123)

    def test_capacity_must_be_positive_integer(self) -> None:
        """Check: capacity must be positive integer."""
        for bad_capacity in (0, -5, 10.5, "40", True):
            with self.assertRaises(rs.InvalidRoomError):
                rs.create_room(self.rooms, "A101", bad_capacity)
        self.assertEqual(self.rooms, {})

    def test_capacity_of_one_is_allowed(self) -> None:
        """Check: capacity of one is allowed."""
        room = rs.create_room(self.rooms, "A101", 1)
        self.assertEqual(room.capacity, 1)

    def test_negative_equipment_count_rejected(self) -> None:
        """Check: negative equipment count rejected."""
        with self.assertRaises(rs.InvalidRoomError):
            rs.create_room(self.rooms, "A101", 40, {"projector": -1})

    def test_non_integer_equipment_count_rejected(self) -> None:
        """Check: non-integer equipment count rejected."""
        for bad_count in ("one", 2.5, True, None):
            with self.assertRaises(rs.InvalidRoomError):
                rs.create_room(
                    self.rooms, "A101", 40, {"projector": bad_count}
                )

    def test_blank_equipment_name_rejected(self) -> None:
        """Check: blank equipment name rejected."""
        for bad_name in (" ", "", 123):
            with self.assertRaises(rs.InvalidRoomError):
                rs.create_room(self.rooms, "A101", 40, {bad_name: 1})


class TestEditRoom(RoomTestCase):
    """Tests for edit_room."""

    def setUp(self) -> None:
        """Create one room to edit."""
        super().setUp()
        rs.create_room(
            self.rooms, "A101", 40, {"projector": 1}, name="Pioneer"
        )

    def test_edit_capacity_only_keeps_equipment_and_name(self) -> None:
        """Check: edit capacity only keeps equipment and name."""
        room = rs.edit_room(self.rooms, "A101", capacity=50)
        self.assertEqual(room.capacity, 50)
        self.assertEqual(room.equipment, {"projector": 1})
        self.assertEqual(room.name, "Pioneer")

    def test_edit_capacity_below_existing_reservation_is_rejected(self) -> None:
        """Check: capacity cannot be lowered below a reserved group size."""
        with self.assertRaises(rs.RoomCapacityConflictError):
            rs.edit_room(
                self.rooms,
                "A101",
                capacity=30,
                largest_reserved_group=35,
            )
        self.assertEqual(self.rooms["A101"].capacity, 40)

    def test_edit_capacity_to_existing_reservation_size_is_allowed(self) -> None:
        """Check: a room can fit a reservation exactly at its new capacity."""
        room = rs.edit_room(
            self.rooms,
            "A101",
            capacity=35,
            largest_reserved_group=35,
        )
        self.assertEqual(room.capacity, 35)

    def test_edit_equipment_only_keeps_capacity_and_name(self) -> None:
        """Check: edit equipment only keeps capacity and name."""
        room = rs.edit_room(self.rooms, "A101", equipment={"mic": 2})
        self.assertEqual(room.capacity, 40)
        self.assertEqual(room.equipment, {"mic": 2})
        self.assertEqual(room.name, "Pioneer")

    def test_edit_name(self) -> None:
        """Check: edit name updates room name."""
        room = rs.edit_room(self.rooms, "A101", name="Voyager")
        self.assertEqual(room.name, "Voyager")
        self.assertEqual(room.capacity, 40)

    def test_edit_missing_room_raises(self) -> None:
        """Check: edit missing room raises."""
        with self.assertRaises(rs.RoomNotFoundError):
            rs.edit_room(self.rooms, "Z999", capacity=10)

    def test_invalid_edit_leaves_room_unchanged(self) -> None:
        """Check: invalid edit leaves room unchanged."""
        with self.assertRaises(rs.InvalidRoomError):
            rs.edit_room(self.rooms, "A101", capacity=0)
        self.assertEqual(self.rooms["A101"].capacity, 40)


class TestDeleteRoom(RoomTestCase):
    """Tests for delete_room."""

    def test_delete_removes_room(self) -> None:
        """Check: delete removes room."""
        rs.create_room(self.rooms, "A101", 40)
        rs.delete_room(self.rooms, "A101")
        self.assertNotIn("A101", self.rooms)

    def test_delete_missing_room_raises(self) -> None:
        """Check: delete missing room raises."""
        with self.assertRaises(rs.RoomNotFoundError):
            rs.delete_room(self.rooms, "A101")

    def test_delete_twice_raises_second_time(self) -> None:
        """Check: delete twice raises second time."""
        rs.create_room(self.rooms, "A101", 40)
        rs.delete_room(self.rooms, "A101")
        with self.assertRaises(rs.RoomNotFoundError):
            rs.delete_room(self.rooms, "A101")


class TestMarkUnavailable(RoomTestCase):
    """Tests for mark_room_unavailable and is_room_available."""

    def setUp(self) -> None:
        """Create a room closed from 10 to 20 October 2026."""
        super().setUp()
        self.room = rs.create_room(self.rooms, "A101", 40)
        rs.mark_room_unavailable(
            self.rooms, "A101", date(2026, 10, 10), date(2026, 10, 20),
            "Renovation",
        )

    def test_reason_is_stored(self) -> None:
        """Check: reason is stored."""
        self.assertEqual(self.room.unavailable_periods[0].reason,
                         "Renovation")

    def test_range_inside_closure_is_unavailable(self) -> None:
        """Check: range inside closure is unavailable."""
        self.assertFalse(rs.is_room_available(
            self.room, date(2026, 10, 12), date(2026, 10, 13)))

    def test_range_before_closure_is_available(self) -> None:
        """Check: range before closure is available."""
        self.assertTrue(rs.is_room_available(
            self.room, date(2026, 10, 1), date(2026, 10, 9)))

    def test_range_after_closure_is_available(self) -> None:
        """Check: range after closure is available."""
        self.assertTrue(rs.is_room_available(
            self.room, date(2026, 10, 21), date(2026, 10, 30)))

    def test_touching_first_day_is_a_clash(self) -> None:
        """Check: touching first day is a clash."""
        self.assertFalse(rs.is_room_available(
            self.room, date(2026, 10, 1), date(2026, 10, 10)))

    def test_touching_last_day_is_a_clash(self) -> None:
        """Check: touching last day is a clash."""
        self.assertFalse(rs.is_room_available(
            self.room, date(2026, 10, 20), date(2026, 10, 25)))

    def test_range_covering_whole_closure_is_a_clash(self) -> None:
        """Check: range covering whole closure is a clash."""
        self.assertFalse(rs.is_room_available(
            self.room, date(2026, 10, 1), date(2026, 10, 30)))

    def test_single_day_closure_is_allowed(self) -> None:
        """Check: single day closure is allowed."""
        rs.mark_room_unavailable(
            self.rooms, "A101", date(2026, 11, 5), date(2026, 11, 5))
        self.assertFalse(rs.is_room_available(
            self.room, date(2026, 11, 5), date(2026, 11, 5)))

    def test_end_before_start_rejected(self) -> None:
        """Check: end before start rejected."""
        with self.assertRaises(rs.InvalidRoomError):
            rs.mark_room_unavailable(
                self.rooms, "A101", date(2026, 12, 2), date(2026, 12, 1))

    def test_missing_room_raises(self) -> None:
        """Check: missing room raises."""
        with self.assertRaises(rs.RoomNotFoundError):
            rs.mark_room_unavailable(
                self.rooms, "Z999", date(2026, 12, 1), date(2026, 12, 2))


class TestFindAvailableRooms(RoomTestCase):
    """Tests for find_available_rooms."""

    def setUp(self) -> None:
        """Create three rooms of different sizes and equipment."""
        super().setUp()
        rs.create_room(self.rooms, "A101", 30, {"projector": 1})
        rs.create_room(self.rooms, "B201", 60, {"projector": 2, "mic": 1})
        rs.create_room(self.rooms, "C301", 100)
        self.start = date(2026, 10, 12)
        self.end = date(2026, 10, 16)

    def ids(self, rooms) -> list:
        """Return the ids of a list of rooms."""
        return [room.room_id for room in rooms]

    def test_filters_by_capacity(self) -> None:
        """Check: filters by capacity."""
        result = rs.find_available_rooms(self.rooms, 50, self.start, self.end)
        self.assertEqual(self.ids(result), ["B201", "C301"])

    def test_group_exactly_equal_to_capacity_fits(self) -> None:
        """Check: group exactly equal to capacity fits."""
        result = rs.find_available_rooms(self.rooms, 30, self.start, self.end)
        self.assertIn("A101", self.ids(result))

    def test_group_one_over_capacity_does_not_fit(self) -> None:
        """Check: group one over capacity does not fit."""
        result = rs.find_available_rooms(self.rooms, 31, self.start, self.end)
        self.assertNotIn("A101", self.ids(result))

    def test_filters_by_equipment(self) -> None:
        """Check: filters by equipment."""
        result = rs.find_available_rooms(
            self.rooms, 10, self.start, self.end, {"mic": 1})
        self.assertEqual(self.ids(result), ["B201"])

    def test_equipment_count_must_be_enough(self) -> None:
        """Check: equipment count must be enough."""
        result = rs.find_available_rooms(
            self.rooms, 10, self.start, self.end, {"projector": 2})
        self.assertEqual(self.ids(result), ["B201"])

    def test_excludes_rooms_closed_in_range(self) -> None:
        """Check: excludes rooms closed in range."""
        rs.mark_room_unavailable(
            self.rooms, "A101", date(2026, 10, 14), date(2026, 10, 15))
        result = rs.find_available_rooms(self.rooms, 10, self.start, self.end)
        self.assertNotIn("A101", self.ids(result))

    def test_results_keep_insertion_order(self) -> None:
        """Results come back in the order rooms were added (no sort)."""
        result = rs.find_available_rooms(self.rooms, 10, self.start, self.end)
        self.assertEqual(self.ids(result), ["A101", "B201", "C301"])

    def test_no_match_returns_empty_list(self) -> None:
        """Check: no match returns empty list."""
        result = rs.find_available_rooms(self.rooms, 500, self.start,
                                         self.end)
        self.assertEqual(result, [])

    def test_deleted_room_not_returned(self) -> None:
        """Check: deleted room not returned."""
        rs.delete_room(self.rooms, "A101")
        result = rs.find_available_rooms(self.rooms, 10, self.start, self.end)
        self.assertNotIn("A101", self.ids(result))

    def test_invalid_group_size_rejected(self) -> None:
        """Check: invalid group size rejected."""
        for bad_size in (0, -1, 10.5, "20", True):
            with self.assertRaises(rs.InvalidRoomError):
                rs.find_available_rooms(
                    self.rooms, bad_size, self.start, self.end
                )

    def test_reversed_dates_rejected(self) -> None:
        """Check: reversed dates rejected."""
        with self.assertRaises(rs.InvalidRoomError):
            rs.find_available_rooms(self.rooms, 10, self.end, self.start)


class TestRecommendRoom(RoomTestCase):
    """Tests for recommend_room."""

    def setUp(self) -> None:
        """Create rooms added in non-sorted order."""
        super().setUp()
        rs.create_room(self.rooms, "C301", 100)
        rs.create_room(self.rooms, "A101", 30, {"projector": 1})
        rs.create_room(self.rooms, "B201", 60, {"mic": 1})
        self.start = date(2026, 10, 12)
        self.end = date(2026, 10, 16)

    def test_recommends_smallest_fitting_room(self) -> None:
        """The tightest fit wins even if it was added later."""
        room = rs.recommend_room(self.rooms, 20, self.start, self.end)
        self.assertEqual(room.room_id, "A101")

    def test_skips_rooms_that_are_too_small(self) -> None:
        """A room below the group size is never recommended."""
        room = rs.recommend_room(self.rooms, 50, self.start, self.end)
        self.assertEqual(room.room_id, "B201")

    def test_respects_equipment(self) -> None:
        """Only rooms with the required equipment are considered."""
        room = rs.recommend_room(
            self.rooms, 20, self.start, self.end, {"mic": 1})
        self.assertEqual(room.room_id, "B201")

    def test_skips_closed_room(self) -> None:
        """A room closed in the range is not recommended."""
        rs.mark_room_unavailable(
            self.rooms, "A101", date(2026, 10, 13), date(2026, 10, 13))
        room = rs.recommend_room(self.rooms, 20, self.start, self.end)
        self.assertEqual(room.room_id, "B201")

    def test_tie_broken_by_room_id(self) -> None:
        """Equal capacities fall back to the lowest room id."""
        rs.create_room(self.rooms, "A102", 30)
        room = rs.recommend_room(self.rooms, 20, self.start, self.end)
        self.assertEqual(room.room_id, "A101")

    def test_returns_none_when_nothing_matches(self) -> None:
        """No matching room gives None, not an error."""
        room = rs.recommend_room(self.rooms, 500, self.start, self.end)
        self.assertIsNone(room)

    def test_invalid_inputs_rejected(self) -> None:
        """Bad group size or reversed dates raise InvalidRoomError."""
        for bad_size in (0, -1, 10.5, "20", True):
            with self.assertRaises(rs.InvalidRoomError):
                rs.recommend_room(self.rooms, bad_size, self.start, self.end)
        with self.assertRaises(rs.InvalidRoomError):
            rs.recommend_room(self.rooms, 10, self.end, self.start)


class TestSeedRooms(RoomTestCase):
    """Tests for load_cmkl_rooms."""

    def test_load_cmkl_rooms_populates_catalog(self) -> None:
        """Check: load cmkl rooms populates official rooms."""
        load_cmkl_rooms(self.rooms)
        self.assertIn("601", self.rooms)
        self.assertEqual(self.rooms["601"].name, "Pioneer")
        self.assertEqual(self.rooms["608"].name, "Bridge")
        self.assertEqual(self.rooms["608"].capacity, 60)
        self.assertEqual(len(self.rooms), 10)


if __name__ == "__main__":
    unittest.main()
