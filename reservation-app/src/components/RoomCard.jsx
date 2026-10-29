// file: src/components/RoomCard.jsx
// purpose: Displays classroom card with room type, equipment, closures, and actions
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React from 'react';

const EQUIPMENT_LABELS = [
  ['projector', 'Projector', 'Projectors'],
  ['whiteboard', 'Whiteboard', 'Whiteboards'],
  ['computers', 'PC', 'PCs'],
  ['mic', 'Mic', 'Mics'],
  ['tv_screen', 'TV', 'TVs'],
];

/**
 * Turn an equipment map into short labels, e.g. { whiteboard: 2 } -> ['2 Whiteboards'].
 * @param {Object} equipment - Equipment counts keyed by type.
 * @returns {string[]} Human-readable equipment labels.
 */
function describeEquipment(equipment = {}) {
  return EQUIPMENT_LABELS.filter(([key]) => equipment[key] > 0).map(
    ([key, singular, plural]) =>
      equipment[key] === 1 ? singular : `${equipment[key]} ${plural}`
  );
}

const STAFF_ACTION =
  'px-2.5 py-2 rounded-md text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors';

/**
 * Card displaying individual classroom details and role-aware action buttons.
 * @param {Object} props
 * @param {Object} props.room - Normalized room object.
 * @param {Object|null} props.currentUser - Active user profile.
 * @param {function} props.onBookClick - Invoked when user wants to book.
 * @param {function} [props.onEditClick] - Staff edit callback.
 * @param {function} [props.onDeleteClick] - Staff delete callback.
 * @param {function} [props.onUnavailClick] - Staff mark unavailable callback.
 * @returns {JSX.Element} The RoomCard component.
 */
export default function RoomCard({
  room,
  currentUser,
  onBookClick,
  onEditClick,
  onDeleteClick,
  onUnavailClick,
}) {
  const isStaff = currentUser?.role === 'Staff';
  const roomNumber = room.room_id || room.id;
  const equipment = describeEquipment(room.equipment);
  const showName =
    room.name && room.name.toLowerCase() !== `room ${roomNumber}`.toLowerCase();

  return (
    <article className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 flex flex-col">
      <div className="p-4 flex-grow space-y-2">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white tabular-nums">
            {roomNumber}
            {showName && (
              <span className="ml-2 text-sm font-normal text-slate-500 dark:text-slate-400">
                {room.name}
              </span>
            )}
          </h3>
          <span
            className={`text-xs font-medium shrink-0 ${
              room.isAvailable
                ? 'text-green-700 dark:text-green-400'
                : 'text-red-700 dark:text-red-400'
            }`}
          >
            {room.isAvailable ? 'Available' : 'Closed'}
          </span>
        </div>

        <p className="text-sm text-slate-700 dark:text-slate-200 tabular-nums">
          {room.room_type || 'Classroom'} · <strong className="font-semibold">{room.capacity}</strong> seats
        </p>

        <p className="text-xs text-slate-500 dark:text-slate-400">
          {equipment.length > 0 ? equipment.join(' · ') : 'No listed equipment'}
        </p>

        {room.description && (
          <p className="text-xs text-slate-500 dark:text-slate-400">{room.description}</p>
        )}

        {!room.isAvailable && room.closureReason && (
          <p className="pt-2 border-t border-slate-100 dark:border-slate-700 text-xs text-red-700 dark:text-red-300 tabular-nums">
            Closed: {room.closureReason}
            {room.activeClosure && ` (until ${room.activeClosure.end_date})`}
          </p>
        )}
      </div>

      <div className="px-4 py-3 border-t border-slate-100 dark:border-slate-700 flex items-center gap-1">
        <button
          id={`book-room-${roomNumber}`}
          onClick={() => onBookClick(room)}
          disabled={!room.isAvailable}
          className="px-4 py-2 rounded-md text-sm font-medium bg-brand-600 hover:bg-brand-700 text-white transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:bg-slate-200 disabled:text-slate-500 dark:disabled:bg-slate-700 dark:disabled:text-slate-400 disabled:cursor-not-allowed"
        >
          {room.isAvailable ? 'Book' : 'Unavailable'}
        </button>

        {isStaff && (
          <div className="ml-auto flex items-center">
            <button
              onClick={() => onEditClick && onEditClick(room)}
              aria-label={`Edit room ${roomNumber}`}
              className={STAFF_ACTION}
            >
              Edit
            </button>
            <button
              onClick={() => onUnavailClick && onUnavailClick(room)}
              aria-label={`Close room ${roomNumber} for a date range`}
              className={STAFF_ACTION}
            >
              Close
            </button>
            <button
              onClick={() => onDeleteClick && onDeleteClick(room)}
              aria-label={`Delete room ${roomNumber}`}
              className={`${STAFF_ACTION} hover:text-red-700 dark:hover:text-red-400`}
            >
              Delete
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
