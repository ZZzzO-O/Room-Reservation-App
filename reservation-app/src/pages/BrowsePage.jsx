// file: src/pages/BrowsePage.jsx
// purpose: Room browsing view with category tabs, typed capacity, live search, and staff controls
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useMemo } from 'react';
import {
  Search,
  Users,
  Monitor,
  Plus,
  CheckSquare,
  Laptop,
  BookOpen,
  FlaskConical,
  Briefcase,
  LayoutGrid,
} from 'lucide-react';

import RoomCard from '../components/RoomCard';
import RoomModal from '../components/RoomModal';
import UnavailabilityModal from '../components/UnavailabilityModal';
import { deleteRoom } from '../api/roomApi';

const CATEGORY_TABS = [
  { key: 'ALL', label: 'All Spaces', icon: LayoutGrid },
  { key: 'Classroom', label: 'Classrooms', icon: BookOpen },
  { key: 'Student Lab', label: 'Student Lab (Voyager)', icon: FlaskConical },
  { key: 'Computer Lab', label: 'Computer Lab (Cube)', icon: Laptop },
  { key: 'Meeting Room', label: 'Meeting Rooms', icon: Briefcase },
];

/**
 * Main classroom browsing dashboard.
 * @param {Object} props
 * @param {Object[]} props.rooms - Array of normalized rooms.
 * @param {Object|null} props.currentUser - Active user.
 * @param {function} props.onBookClick - Handler when user clicks Book.
 * @param {function} props.onRefreshRooms - Handler to refetch rooms after CRUD.
 * @returns {JSX.Element} The BrowsePage component.
 */
export default function BrowsePage({
  rooms,
  currentUser,
  onBookClick,
  onRefreshRooms,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [minCapacity, setMinCapacity] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [needsProjector, setNeedsProjector] = useState(false);
  const [needsWhiteboard, setNeedsWhiteboard] = useState(false);
  const [needsComputers, setNeedsComputers] = useState(false);

  // Modal states
  const [isRoomModalOpen, setIsRoomModalOpen] = useState(false);
  const [roomToEdit, setRoomToEdit] = useState(null);
  const [unavailRoom, setUnavailRoom] = useState(null);
  const [deleteTargetRoom, setDeleteTargetRoom] = useState(null);
  const [deleteError, setDeleteError] = useState('');

  const isStaff = currentUser?.role === 'Staff';

  /**
   * Filter rooms by room number/ID, name, category, capacity, and equipment.
   * Sorted naturally by room number.
   */
  const filteredRooms = useMemo(() => {
    return rooms
      .filter((room) => {
        const q = searchQuery.toLowerCase().trim();
        const roomIdStr = String(room.room_id || room.id).toLowerCase();
        const matchesSearch =
          !q ||
          roomIdStr.includes(q) ||
          `room ${roomIdStr}`.includes(q) ||
          room.name.toLowerCase().includes(q) ||
          (room.description && room.description.toLowerCase().includes(q));

        const matchesCategory =
          selectedCategory === 'ALL' || room.room_type === selectedCategory;

        const cap = parseInt(minCapacity, 10);
        const matchesCapacity = isNaN(cap) || room.capacity >= cap;

        const matchesProjector = !needsProjector || room.hasProjector;
        const matchesWhiteboard = !needsWhiteboard || room.hasWhiteboard;
        const matchesComputers = !needsComputers || room.hasComputers;

        return (
          matchesSearch &&
          matchesCategory &&
          matchesCapacity &&
          matchesProjector &&
          matchesWhiteboard &&
          matchesComputers
        );
      })
      .sort((a, b) => {
        const numA = parseInt(a.room_id || a.id, 10);
        const numB = parseInt(b.room_id || b.id, 10);
        if (!isNaN(numA) && !isNaN(numB)) {
          return numA - numB;
        }
        return String(a.room_id || a.id).localeCompare(String(b.room_id || b.id));
      });
  }, [
    rooms,
    searchQuery,
    selectedCategory,
    minCapacity,
    needsProjector,
    needsWhiteboard,
    needsComputers,
  ]);

  /** Open modal to create a new room. */
  const handleOpenAddRoom = () => {
    setRoomToEdit(null);
    setIsRoomModalOpen(true);
  };

  /** Open modal to edit an existing room. */
  const handleOpenEditRoom = (room) => {
    setRoomToEdit(room);
    setIsRoomModalOpen(true);
  };

  /** Open modal to mark room closed. */
  const handleOpenUnavail = (room) => {
    setUnavailRoom(room);
  };

  /** Handle room deletion request. */
  const handleConfirmDeleteRoom = async () => {
    if (!deleteTargetRoom) return;
    setDeleteError('');
    try {
      await deleteRoom(deleteTargetRoom.room_id || deleteTargetRoom.id);
      setDeleteTargetRoom(null);
      onRefreshRooms();
    } catch (err) {
      setDeleteError(err.message || 'Cannot delete room with active reservations.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Search Filter Bar */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 transition-colors space-y-4">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              CMKL Campus Spaces
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Official catalog of classrooms, student labs, and meeting facilities for Fall 2026.
            </p>
          </div>

          {isStaff && (
            <button
              id="btn-add-room"
              onClick={handleOpenAddRoom}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition-colors shrink-0"
            >
              <Plus className="w-4 h-4" />
              Add Room
            </button>
          )}
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-700/60">
          {CATEGORY_TABS.map((tab) => {
            const Icon = tab.icon;
            const isSelected = selectedCategory === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setSelectedCategory(tab.key)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Filter Controls */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2">
          {/* Search bar prioritized for room numbers */}
          <div className="md:col-span-5 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              id="search-rooms"
              type="text"
              placeholder="Search room number (e.g. 604, 609, 601) or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          {/* Typed Capacity Input */}
          <div className="md:col-span-3 relative">
            <Users className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 pointer-events-none" />
            <input
              id="filter-capacity"
              type="number"
              min="1"
              placeholder="Min seats (e.g. 35)"
              value={minCapacity}
              onChange={(e) => setMinCapacity(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          {/* Equipment Checkboxes */}
          <div className="md:col-span-4 flex flex-wrap items-center gap-2">
            <label
              htmlFor="filter-projector"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium cursor-pointer border transition-colors select-none ${
                needsProjector
                  ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
                  : 'bg-slate-50 border-slate-200 text-slate-600 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-400'
              }`}
            >
              <input
                id="filter-projector"
                type="checkbox"
                checked={needsProjector}
                onChange={(e) => setNeedsProjector(e.target.checked)}
                className="hidden"
              />
              <Monitor className="w-3.5 h-3.5" /> Projector
            </label>

            <label
              htmlFor="filter-whiteboard"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium cursor-pointer border transition-colors select-none ${
                needsWhiteboard
                  ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
                  : 'bg-slate-50 border-slate-200 text-slate-600 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-400'
              }`}
            >
              <input
                id="filter-whiteboard"
                type="checkbox"
                checked={needsWhiteboard}
                onChange={(e) => setNeedsWhiteboard(e.target.checked)}
                className="hidden"
              />
              <CheckSquare className="w-3.5 h-3.5" /> Whiteboard
            </label>

            <label
              htmlFor="filter-computers"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium cursor-pointer border transition-colors select-none ${
                needsComputers
                  ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
                  : 'bg-slate-50 border-slate-200 text-slate-600 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-400'
              }`}
            >
              <input
                id="filter-computers"
                type="checkbox"
                checked={needsComputers}
                onChange={(e) => setNeedsComputers(e.target.checked)}
                className="hidden"
              />
              <Laptop className="w-3.5 h-3.5" /> Lab Computers
            </label>
          </div>
        </div>
      </div>

      {/* Classrooms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredRooms.length > 0 ? (
          filteredRooms.map((room) => (
            <RoomCard
              key={room.room_id || room.id}
              room={room}
              currentUser={currentUser}
              onBookClick={onBookClick}
              onEditClick={handleOpenEditRoom}
              onDeleteClick={(r) => setDeleteTargetRoom(r)}
              onUnavailClick={handleOpenUnavail}
            />
          ))
        ) : (
          <div className="col-span-full py-16 text-center bg-white dark:bg-slate-800 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700">
            <Search className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              No matching spaces found
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Try adjusting your category selection, seat capacity, or equipment filters.
            </p>
          </div>
        )}
      </div>

      {/* Room Add / Edit Modal */}
      {isRoomModalOpen && (
        <RoomModal
          isOpen={isRoomModalOpen}
          room={roomToEdit}
          onClose={() => setIsRoomModalOpen(false)}
          onSuccess={onRefreshRooms}
        />
      )}

      {/* Mark Unavailable Modal */}
      {unavailRoom && (
        <UnavailabilityModal
          isOpen={Boolean(unavailRoom)}
          room={unavailRoom}
          onClose={() => setUnavailRoom(null)}
          onSuccess={onRefreshRooms}
        />
      )}

      {/* Delete Room Confirmation Modal */}
      {deleteTargetRoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 border border-slate-200 dark:border-slate-700">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Delete Room {deleteTargetRoom.name}?
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              This will remove the room from the campus catalog. If active reservations exist for this room, deletion will be rejected.
            </p>
            {deleteError && (
              <div className="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-xs">
                {deleteError}
              </div>
            )}
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteTargetRoom(null)}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDeleteRoom}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
