// file: src/components/RoomCard.jsx
// purpose: Displays classroom card with category badges, equipment, closures, and actions
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React from 'react';
import {
  Users,
  Monitor,
  MapPin,
  Edit3,
  Trash2,
  CalendarX,
  BookOpen,
  FlaskConical,
  Laptop,
  Briefcase,
} from 'lucide-react';

/**
 * Render category badge with appropriate icon and styling.
 * @param {string} roomType - Type of room ('Classroom' | 'Lab' | 'Computer Lab' | 'Meeting Room').
 * @returns {JSX.Element} Category pill.
 */
function renderTypeBadge(roomType) {
  switch (roomType) {
    case 'Lab':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
          <FlaskConical className="w-3 h-3" />
          Lab
        </span>
      );
    case 'Computer Lab':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-200 dark:border-purple-800/60">
          <Laptop className="w-3 h-3" />
          Computer Lab
        </span>
      );
    case 'Meeting Room':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
          <Briefcase className="w-3 h-3" />
          Meeting Room
        </span>
      );
    case 'Classroom':
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60">
          <BookOpen className="w-3 h-3" />
          Classroom
        </span>
      );
  }
}

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

  /** Format equipment as formatted pill elements. */
  const equipmentItems = (() => {
    const eq = room.equipment || {};
    const items = [];
    if (eq.projector) items.push(`Projector x${eq.projector}`);
    if (eq.whiteboard) items.push(`Whiteboard x${eq.whiteboard}`);
    if (eq.computers) items.push(`PCs x${eq.computers}`);
    if (eq.mic) items.push(`Mic x${eq.mic}`);
    if (eq.tv_screen) items.push(`TV x${eq.tv_screen}`);
    return items;
  })();

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col justify-between transition-all hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500">
      {/* Card Header & Body */}
      <div className="p-5 flex-grow space-y-3">
        <div className="flex justify-between items-start gap-2">
          <div>
            <div className="flex items-baseline gap-2 mb-1.5 flex-wrap">
              <h3 className="font-extrabold text-xl text-slate-900 dark:text-white leading-tight tracking-tight">
                Room {room.room_id || room.id}
              </h3>
              {room.name && room.name.toLowerCase() !== `room ${room.room_id || room.id}`.toLowerCase() && (
                <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                  {room.name}
                </span>
              )}
            </div>
            {renderTypeBadge(room.room_type)}
          </div>

          <span
            className={`px-2.5 py-1 text-xs font-semibold rounded-full shrink-0 transition-colors ${
              room.isAvailable
                ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
                : 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
            }`}
          >
            {room.isAvailable ? 'Available' : 'Closed'}
          </span>
        </div>

        {/* Room Description / Note */}
        {room.description && (
          <p className="text-xs text-slate-500 dark:text-slate-400 italic">
            {room.description}
          </p>
        )}

        {/* Closure details if unavailable */}
        {!room.isAvailable && room.closureReason && (
          <div className="p-2.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 rounded-xl text-xs text-rose-700 dark:text-rose-300">
            <span className="font-semibold">Reason:</span> {room.closureReason}
            {room.activeClosure && (
              <span className="block text-rose-500 text-[11px] mt-0.5">
                Until {room.activeClosure.end_date}
              </span>
            )}
          </div>
        )}

        <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300 pt-1">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-slate-400 shrink-0" />
            <span>Capacity: <strong className="text-slate-900 dark:text-white">{room.capacity}</strong> seats</span>
          </div>

          <div className="flex items-start gap-2">
            <Monitor className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div className="flex flex-wrap gap-1">
              {equipmentItems.length > 0 ? (
                equipmentItems.map((item, idx) => (
                  <span
                    key={idx}
                    className="inline-block px-2 py-0.5 bg-slate-100 dark:bg-slate-700/60 text-slate-700 dark:text-slate-300 rounded text-xs font-medium"
                  >
                    {item}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400 italic">Standard furnishings</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-xs text-slate-500 dark:text-slate-400">CMKL Campus</span>
          </div>
        </div>
      </div>

      {/* Staff Actions Bar */}
      {isStaff && (
        <div className="px-5 py-2 bg-slate-50 dark:bg-slate-900/60 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Staff Controls:</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onEditClick && onEditClick(room)}
              title="Edit Room"
              className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onUnavailClick && onUnavailClick(room)}
              title="Mark Closed / Renovation"
              className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/30 rounded-lg transition-colors"
            >
              <CalendarX className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onDeleteClick && onDeleteClick(room)}
              title="Delete Room"
              className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Card Action */}
      <div className="p-4 bg-slate-50/70 dark:bg-slate-800/80 border-t border-slate-100 dark:border-slate-700">
        <button
          id={`book-room-${room.room_id || room.id}`}
          onClick={() => onBookClick(room)}
          disabled={!room.isAvailable}
          className={`w-full py-2 px-4 rounded-xl font-medium text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            room.isAvailable
              ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 dark:focus:ring-offset-slate-800 shadow-sm'
              : 'bg-slate-200 dark:bg-slate-700/70 text-slate-400 dark:text-slate-500 cursor-not-allowed'
          }`}
        >
          {room.isAvailable ? 'Book Room' : 'Currently Unavailable'}
        </button>
      </div>
    </div>
  );
}