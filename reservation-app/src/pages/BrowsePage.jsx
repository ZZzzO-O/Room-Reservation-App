// file: src/pages/BrowsePage.jsx
// purpose: Room browsing view with category tabs, typed capacity, live search, and staff controls
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useMemo } from 'react';
import { Search, X } from 'lucide-react';

import RoomCard from '../components/RoomCard';
import RoomModal from '../components/RoomModal';
import UnavailabilityModal from '../components/UnavailabilityModal';
import ModalShell from '../components/ModalShell';
import { deleteRoom } from '../api/roomApi';
import { INPUT, BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER, ERROR_BOX } from '../utils/styles';

const CATEGORY_TABS = [
  { key: 'ALL', label: 'All' },
  { key: 'Classroom', label: 'Classrooms' },
  { key: 'Lab', label: 'Labs' },
  { key: 'Computer Lab', label: 'Computer lab' },
  { key: 'Meeting Room', label: 'Meeting rooms' },
];

/**
 * Checkbox used for the equipment filters.
 * @param {Object} props
 * @param {string} props.id - Input id.
 * @param {string} props.label - Visible label.
 * @param {boolean} props.checked - Current state.
 * @param {function} props.onChange - Called with the new checked value.
 * @returns {JSX.Element} The filter toggle.
 */
function FilterToggle({ id, label, checked, onChange }) {
  return (
    <label
      htmlFor={id}
      className="inline-flex items-center gap-2 px-1 py-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer select-none"
    >
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 accent-brand-600"
      />
      {label}
    </label>
  );
}

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

  const handleOpenAddRoom = () => {
    setRoomToEdit(null);
    setIsRoomModalOpen(true);
  };

  const handleOpenEditRoom = (room) => {
    setRoomToEdit(room);
    setIsRoomModalOpen(true);
  };

  const handleOpenUnavail = (room) => {
    setUnavailRoom(room);
  };

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

  const segmentClass = (isSelected) =>
    `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
      isSelected
        ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
    }`;

  const closeDeleteDialog = () => {
    setDeleteTargetRoom(null);
    setDeleteError('');
  };

  return (
    <div className="space-y-5">
      <header className="flex flex-col sm:flex-row justify-between sm:items-end gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Rooms
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 tabular-nums">
            {filteredRooms.length === rooms.length
              ? `${rooms.length} bookable rooms · Fall 2026`
              : `Showing ${filteredRooms.length} of ${rooms.length} rooms`}
          </p>
        </div>

        {isStaff && (
          <button id="btn-add-room" onClick={handleOpenAddRoom} className={`${BTN_PRIMARY} shrink-0`}>
            Add room
          </button>
        )}
      </header>

      <section
        aria-label="Filters"
        className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-3"
      >
        <div
          role="tablist"
          aria-label="Room type"
          className="inline-flex flex-wrap gap-0.5 p-0.5 rounded-lg bg-slate-100 dark:bg-slate-900"
        >
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={selectedCategory === tab.key}
              onClick={() => setSelectedCategory(tab.key)}
              className={segmentClass(selectedCategory === tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <div className="relative md:w-80">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 pointer-events-none"
              aria-hidden="true"
            />
            <input
              id="search-rooms"
              type="search"
              aria-label="Search rooms"
              placeholder="Room number or name, e.g. 604"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`${INPUT} pl-9 pr-9`}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-1 top-1/2 -translate-y-1/2 p-2 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-100"
                aria-label="Clear room search"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            )}
          </div>

          <div className="md:w-36">
            <input
              id="filter-capacity"
              type="number"
              min="1"
              aria-label="Minimum seats"
              placeholder="Min. seats"
              value={minCapacity}
              onChange={(e) => setMinCapacity(e.target.value)}
              className={INPUT}
            />
          </div>

          <div className="flex flex-wrap items-center gap-x-4">
            <FilterToggle
              id="filter-projector"
              label="Projector"
              checked={needsProjector}
              onChange={setNeedsProjector}
            />
            <FilterToggle
              id="filter-whiteboard"
              label="Whiteboard"
              checked={needsWhiteboard}
              onChange={setNeedsWhiteboard}
            />
            <FilterToggle
              id="filter-computers"
              label="Computers"
              checked={needsComputers}
              onChange={setNeedsComputers}
            />
          </div>
        </div>
      </section>

      {filteredRooms.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredRooms.map((room) => (
            <RoomCard
              key={room.room_id || room.id}
              room={room}
              currentUser={currentUser}
              onBookClick={onBookClick}
              onEditClick={handleOpenEditRoom}
              onDeleteClick={(r) => setDeleteTargetRoom(r)}
              onUnavailClick={handleOpenUnavail}
            />
          ))}
        </div>
      ) : (
        <div className="py-12 text-center rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            No rooms match these filters.
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Try a smaller seat count or fewer equipment requirements.
          </p>
        </div>
      )}

      {isRoomModalOpen && (
        <RoomModal
          isOpen={isRoomModalOpen}
          room={roomToEdit}
          onClose={() => setIsRoomModalOpen(false)}
          onSuccess={onRefreshRooms}
        />
      )}

      {unavailRoom && (
        <UnavailabilityModal
          isOpen={Boolean(unavailRoom)}
          room={unavailRoom}
          onClose={() => setUnavailRoom(null)}
          onSuccess={onRefreshRooms}
        />
      )}

      {deleteTargetRoom && (
        <ModalShell
          title={`Delete room ${deleteTargetRoom.room_id || deleteTargetRoom.id}?`}
          onClose={closeDeleteDialog}
        >
          <div className="p-5 space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-300">
              {deleteTargetRoom.name || 'This room'} will be removed from the catalog. Rooms
              with reservations can’t be deleted.
            </p>
            {deleteError && <div className={ERROR_BOX}>{deleteError}</div>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={closeDeleteDialog} className={BTN_SECONDARY}>
                Cancel
              </button>
              <button type="button" onClick={handleConfirmDeleteRoom} className={BTN_DANGER}>
                Delete room
              </button>
            </div>
          </div>
        </ModalShell>
      )}
    </div>
  );
}
